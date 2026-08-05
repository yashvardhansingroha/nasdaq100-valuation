# NASDAQ-100 Intrinsic Value & Market Intelligence Platform

Professional-grade quantitative equity research platform that estimates the intrinsic value of the NASDAQ-100 index by valuing every constituent individually.

**Core principle: Intrinsic Value ≠ Market Sentiment** — valuation uses only fundamentals; sentiment is reported separately.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure optional API keys
copy .env.example .env

# Run full pipeline (constituents → valuation → sentiment → DB → reports)
python main.py --mode full

# Launch dashboard
streamlit run dashboard/dashboard.py
```

## CLI Modes

| Mode | Description |
|------|-------------|
| `full` | Complete pipeline: valuation + sentiment + reports |
| `valuation` | Valuation only (no sentiment) |
| `constituents` | Refresh NASDAQ-100 weights cache |
| `sentiment` | Sentiment analysis only |

## Windows Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Set trigger: Daily at 6:30 AM (or your preferred time)
3. Action: Start a program → `C:\Users\ysing\Projects\nasdaq100-valuation\run_daily.bat`
4. Or run the scheduler daemon: `python scheduler/scheduler.py`

## Project Structure

```
nasdaq100-valuation/
├── valuation/        # DCF, multiples, blended, confidence (fundamentals only)
├── market/           # Sentiment modules (isolated from valuation)
├── index/            # Constituents, aggregation, sector analysis
├── meta_portfolio/   # Dynamic multi-strategy allocation engine
├── database/         # SQLAlchemy ORM + SQLite history
├── dashboard/        # Streamlit UI (valuation + meta-portfolio)
├── reports/          # Daily CSV/Excel/PDF output
├── scheduler/        # Automated daily runs
└── tests/            # pytest unit tests
```

## Configuration

All assumptions in `config.py`:
- Discount rate, terminal growth, projection years
- DCF/multiples blend weights
- API keys via `.env`
- Cache TTL, database paths

## Testing

```bash
pytest tests/ -v
```

## Meta-Portfolio Engine

Dynamic multi-strategy allocator across real ETF proxies (**MTUM**, **USMV**, **VIXY**):

- 60-day rolling vol / covariance
- Allocators: inverse-vol, minimum variance, max diversification (net of 10bps turnover)
- Benchmarks: equal-weight and 60/40
- Regime analysis + attribution
- **Finance pack** (IB / general finance): investment memo PDF, Excel workbook, interview prep

```bash
# Run backtest + export Excel + PDF memo (uses cached prices after first download)
python -m meta_portfolio

# Refresh market data
python -m meta_portfolio --force-download

# Interactive dashboard
streamlit run dashboard/meta_portfolio.py
```

Interview deliverables live in [`meta_portfolio/reports/`](meta_portfolio/reports/):

| File | Purpose |
|------|---------|
| `allocation_memo.pdf` | 2–3 page investment memo (club-branded) |
| `meta_portfolio_analysis.xlsx` | Returns, weights, performance, regimes, attribution |
| `QUANT_CLUB.md` | Quant Club one-pager + resume line |
| `quant_club_deck.md` | 5-slide finance-only club deck |
| `STRATEGY_RATIONALE.md` | Factor / macro framing of each sleeve |
| `EXHIBIT_CAPTIONS.md` | One-sentence chart takeaways |
| `INTERVIEW_PREP.md` | 60-sec pitch + likely Q&A |

### Quant Club, BITS Pilani

Independent research case study on multi-strategy portfolio allocation (portfolio construction / risk vertical). Finance-first narrative: sleeves, regimes, mandate trade-offs — not software architecture.

See [`meta_portfolio/reports/QUANT_CLUB.md`](meta_portfolio/reports/QUANT_CLUB.md) and [`allocation_memo.pdf`](meta_portfolio/reports/allocation_memo.pdf).

## License

Private research tool — not financial advice.
