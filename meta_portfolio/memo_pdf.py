"""Generate Investment Memo PDF from backtest results."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from meta_portfolio import config
from meta_portfolio.backtest import BacktestResult
from meta_portfolio.regimes import regime_metrics_table


def _pct(x: float, digits: int = 1) -> str:
    return f"{100.0 * x:.{digits}f}%"


def _num(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}"


def _safe(text: str) -> str:
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2212": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class _MemoPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(
            0,
            8,
            _safe(f"{config.CLUB_NAME} | Page {self.page_no()}"),
            align="C",
        )


def _write(pdf: _MemoPDF, text: str, size: int = 10, style: str = "", color=(0, 0, 0)) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", style, size)
    pdf.set_text_color(*color)
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.multi_cell(usable, 5, _safe(text))
    pdf.set_x(pdf.l_margin)
    pdf.set_text_color(0, 0, 0)


def generate_memo_pdf(
    result: BacktestResult,
    path: str | Path | None = None,
) -> Path:
    """Write a 2-3 page investment memo PDF using live backtest metrics."""
    reports_dir = config.PACKAGE_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = Path(path) if path else reports_dir / "allocation_memo.pdf"

    assert result.metrics is not None
    m = result.metrics
    inv = m.loc["InvVol"]
    ew = m.loc["EqualWeight"]
    b6040 = m.loc["60/40"]
    minvar = m.loc["MinVar"]

    start = result.returns.index.min().date().isoformat()
    end = result.returns.index.max().date().isoformat()
    n_days = len(result.returns)
    regimes = regime_metrics_table(result.portfolio_net)

    pdf = _MemoPDF(format="Letter")
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.set_top_margin(18)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    _write(pdf, config.CLUB_NAME, size=10, style="B", color=(20, 40, 80))
    _write(pdf, config.CASE_STUDY_VERTICAL, size=9, color=(80, 80, 80))
    pdf.ln(1)
    _write(pdf, config.CASE_STUDY_TITLE, size=14, style="B")
    _write(
        pdf,
        f"Author: {config.AUTHOR_NAME} | {config.CASE_STUDY_DATE}",
        size=9,
        color=(80, 80, 80),
    )
    pdf.ln(1)
    _write(
        pdf,
        f"Dynamic risk budgeting across MTUM / USMV / VIXY | "
        f"Sample: {start} to {end} ({n_days} trading days)",
        size=9,
        color=(80, 80, 80),
    )
    pdf.ln(2)

    _write(pdf, "1. Executive Summary", size=11, style="B", color=(20, 40, 80))
    _write(
        pdf,
        (
            f"This case study evaluates how a multi-strategy allocator should distribute capital "
            f"across three liquid strategy sleeves - momentum (MTUM), defensive min-vol (USMV), "
            f"and crisis/vol (VIXY) - using a 60-day rolling risk engine. "
            f"Net of 10bps transaction costs, inverse-volatility allocation delivered "
            f"{_pct(float(inv['Ann. Return']))} annualized return and Sharpe {_num(float(inv['Sharpe']))}, "
            f"versus equal-weight at {_pct(float(ew['Ann. Return']))} and Sharpe {_num(float(ew['Sharpe']))}. "
            f"A static 60/40 (MTUM/USMV) earned the highest return ({_pct(float(b6040['Ann. Return']))}) "
            f"by avoiding VIXY's long-run roll decay. "
            f"Recommendation: use inverse-vol when the mandate is risk-adjusted capital preservation "
            f"with a crisis sleeve; use 60/40 when the mandate is return-seeking and hedges are optional."
        ),
    )

    _write(pdf, "2. Investment Thesis", size=11, style="B", color=(20, 40, 80))
    _write(
        pdf,
        (
            "Multi-strategy hedge funds allocate capital across strategy return streams whose "
            "risk contributions change with market regimes. The core problem is dynamic risk "
            "budgeting: when one sleeve's volatility spikes, capital should shrink there and "
            "rotate toward more stable sleeves - without abandoning diversification. This study "
            "treats publicly traded ETFs as transparent proxies for momentum, defensive, and "
            "crisis strategies, then compares naive inverse-vol risk parity against "
            "covariance-aware minimum variance and max diversification, all versus static benchmarks."
        ),
    )

    _write(pdf, "3. Strategy Sleeves", size=11, style="B", color=(20, 40, 80))
    _write(
        pdf,
        (
            "Momentum (MTUM): equity factor tilt that participates in trending markets; higher beta "
            "and drawdown risk in abrupt reversals. "
            "Defensive / Min-Vol (USMV): low-beta sleeve oriented to capital preservation in "
            "risk-off environments; steadier path, lower upside in strong bulls. "
            "Crisis / Vol (VIXY): short-term VIX futures ETF that tends to rise when equity vol "
            "spikes; provides convexity in crashes but suffers structural roll/contango decay in "
            "calm markets. That decay is the central economic trade-off in this portfolio."
        ),
    )

    _write(pdf, "4. Methodology", size=11, style="B", color=(20, 40, 80))
    _write(
        pdf,
        (
            "Risk window: trailing 60 trading days for annualized volatility and the covariance "
            "matrix. No lookahead - weights for day t use information through t-1 only. "
            "Inverse-vol: weight_i proportional to 1/sigma_i, renormalized to 100% invested "
            "(long-only, no leverage). "
            "Minimum variance: minimize portfolio variance w'Sigma w with sleeve bounds 5%-60%. "
            "Max diversification: maximize (w'sigma) / sqrt(w'Sigma w) under the same bounds. "
            f"Friction: 10bps per unit of one-way turnover on dynamic methods. "
            f"Risk-free rate for Sharpe/Sortino: {_pct(config.RISK_FREE_RATE, 1)}."
        ),
    )

    _write(pdf, "5. Results (Net of Costs)", size=11, style="B", color=(20, 40, 80))
    usable = pdf.w - pdf.l_margin - pdf.r_margin
    col_w = [usable * x for x in (0.22, 0.195, 0.195, 0.195, 0.195)]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(pdf.l_margin)
    for w, h in zip(col_w, ["Method", "Ann Ret", "Sharpe", "Max DD", "VaR 95%"]):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for name in ("InvVol", "MinVar", "MaxDiv", "EqualWeight", "60/40"):
        row = m.loc[name]
        vals = [
            name,
            _pct(float(row["Ann. Return"])),
            _num(float(row["Sharpe"])),
            _pct(float(row["Max Drawdown"])),
            _pct(float(row["VaR 95% (1d)"])),
        ]
        pdf.set_x(pdf.l_margin)
        for w, v in zip(col_w, vals):
            pdf.cell(w, 6, v, border=1)
        pdf.ln()
    pdf.ln(2)
    _write(
        pdf,
        (
            f"InvVol cut max drawdown to {_pct(float(inv['Max Drawdown']))} vs "
            f"{_pct(float(ew['Max Drawdown']))} for equal-weight, and lifted Sharpe from "
            f"{_num(float(ew['Sharpe']))} to {_num(float(inv['Sharpe']))}. "
            f"MinVar was more conservative (vol {_pct(float(minvar['Ann. Vol']))}) but "
            f"lagged InvVol on risk-adjusted return after costs. "
            f"60/40 won on absolute return because it holds zero VIXY. "
            f"InvVol 1-day 95% historical VaR: {_pct(float(inv['VaR 95% (1d)']))}."
        ),
    )

    _write(pdf, "6. Regime Analysis", size=11, style="B", color=(20, 40, 80))
    if not regimes.empty and ("COVID Crash", "InvVol") in regimes.index:
        covid_inv = regimes.loc[("COVID Crash", "InvVol")]
        covid_ew = regimes.loc[("COVID Crash", "EqualWeight")]
        covid_6040 = regimes.loc[("COVID Crash", "60/40")]
        shock_inv = regimes.loc[("2022 Rate Shock", "InvVol")]
        shock_6040 = regimes.loc[("2022 Rate Shock", "60/40")]
        _write(
            pdf,
            (
                f"COVID crash (Feb-Mar 2020): equal-weight's VIXY sleeve produced a large positive "
                f"period return ({_pct(float(covid_ew['Total Return']))}), illustrating crisis "
                f"convexity; 60/40 fell {_pct(float(covid_6040['Total Return']))} without a vol hedge. "
                f"InvVol ({_pct(float(covid_inv['Total Return']))}) sat between pure risk-on and "
                f"equal-weight's heavy VIXY bet. "
                f"2022 rate shock: all sleeves struggled; InvVol returned "
                f"{_pct(float(shock_inv['Total Return']))} vs {_pct(float(shock_6040['Total Return']))} "
                f"for 60/40. In a grinding rates-driven bear, the crisis sleeve helped less than in "
                f"March 2020 - an important mandate implication."
            ),
        )
    else:
        _write(
            pdf,
            "Regime tables are in the Excel workbook (Regimes sheet) and Streamlit dashboard.",
        )

    _write(pdf, "7. Risks and Limitations", size=11, style="B", color=(20, 40, 80))
    _write(
        pdf,
        (
            "VIXY is a futures-based product with roll/contango costs; it is a poor permanent hedge "
            "and a better episodic crisis sleeve. Equal-weight's long-run underperformance is largely "
            "this drag. ETF proxies are not live hedge-fund P&L; they approximate strategy style "
            "exposures only. Daily rebalancing inflates turnover versus institutional "
            f"monthly/quarterly practice (InvVol ann. turnover ~{_num(float(inv['Ann. Turnover']), 1)}x). "
            "Long-only, fully invested, no leverage, no shorting, no cash sleeve. "
            "Past regime performance is not a forecast; 60-day windows can lag abrupt regime shifts."
        ),
    )

    _write(pdf, "8. Conclusion", size=11, style="B", color=(20, 40, 80))
    _write(
        pdf,
        (
            "For a risk-conscious allocator who wants a dedicated crisis sleeve, inverse-volatility "
            "risk parity improves Sharpe and drawdowns versus naive equal-weight after realistic "
            "friction. For a return-seeking mandate that can live without permanent vol exposure, "
            "static 60/40 (momentum + min-vol) dominates on CAGR because it avoids VIXY decay. "
            "The professional takeaway is not that one method always wins - it is that the optimal "
            "allocator depends on whether the investment committee values crisis convexity enough "
            "to pay its carry cost."
        ),
    )

    pdf.ln(2)
    _write(
        pdf,
        (
            "Not financial advice. Research / educational case study only. "
            "See STRATEGY_RATIONALE.md, EXHIBIT_CAPTIONS.md, and INTERVIEW_PREP.md."
        ),
        size=8,
        style="I",
        color=(100, 100, 100),
    )

    pdf.output(str(path))
    return path
