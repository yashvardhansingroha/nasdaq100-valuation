"""Deterministic 60-trading-day backfill into database/history.db (seeded, idempotent).

Anchors on the latest real snapshot in the DB (or rebuilds one offline from cached
fundamentals + the xlsx report when the DB is empty) and simulates market prices
varying around intrinsic values with a seeded gap walk converging to the anchor close.
"""
import json, sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

import config
from database.schema import get_session_factory
from market.sentiment_engine import deterministic_scores
from utils.models import CompanyFinancials
from valuation.blended_valuation import blend_valuation
from valuation.confidence_model import compute_confidence
from valuation.dcf_model import run_dcf
from valuation.multiples_model import compute_sector_medians, run_multiples

SEED, DAYS = 20260809, 60
CONST_COLS = ["dcf_value", "multiples_value", "blended_value", "blended_bear_value", "blended_base_value", "blended_bull_value", "valuation_method", "confidence_score", "sector", "dcf_bear_value", "dcf_base_value", "dcf_bull_value"]

def _cols(con, table, skip):
    return [r[1] for r in con.execute(f"PRAGMA table_info({table})") if r[1] not in skip]

def _anchor_from_cache():
    """Rebuild the anchor company snapshot offline from cached JSON fundamentals."""
    weights = pd.read_csv(config.CONSTITUENTS_CSV)
    fmap = {t: CompanyFinancials(**json.loads((Path(config.CACHE_DIR) / f"financials_{t}.json").read_text(encoding="utf-8")))
            for t in weights["ticker"] if (Path(config.CACHE_DIR) / f"financials_{t}.json").exists()}
    medians, rows = compute_sector_medians(fmap), []
    for _, c in weights.iterrows():
        fin = fmap.get(c["ticker"])
        if fin is None or not fin.price:
            continue
        dcf, mult = run_dcf(fin), run_multiples(fin, medians)[0]
        b = blend_valuation(fin.price, dcf.value, mult, dcf.bear_value, dcf.base_value, dcf.bull_value)
        conf, _ = compute_confidence(fin, dcf.value, mult)
        rows.append({"ticker": c["ticker"], "price": fin.price, "dcf_value": dcf.value, "multiples_value": mult,
                     "blended_value": b.blended_value, "blended_bear_value": b.blended_bear_value, "blended_base_value": b.blended_base_value,
                     "blended_bull_value": b.blended_bull_value, "upside": b.upside, "valuation_method": b.valuation_method,
                     "confidence_score": conf, "sector": c["sector"], "market_cap": c["market_cap"], "index_weight": c["index_weight"],
                     "dcf_bear_value": dcf.bear_value, "dcf_base_value": dcf.base_value, "dcf_bull_value": dcf.bull_value})
    return pd.DataFrame(rows), str(weights["as_of_date"].iloc[0])

def build_history():
    """Rebuild DAYS trading days of company, index, and sentiment history."""
    Path(config.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    get_session_factory(config.DATABASE_PATH)  # creates tables + applies migrations
    con = sqlite3.connect(config.DATABASE_PATH)
    anchor = pd.read_sql("SELECT * FROM daily_company_values WHERE date=(SELECT MAX(date) FROM daily_company_values)", con)
    if anchor.empty:
        reports = sorted(Path(config.REPORTS_DIR).glob("nasdaq100_*.xlsx"))
        anchor, as_of = _anchor_from_cache()
        if reports:
            index_price = float(pd.read_excel(reports[-1], sheet_name="Overview")["index_price"].iloc[0])
        else:
            index_price = 29722.30
    else:
        idx = pd.read_sql("SELECT * FROM daily_index ORDER BY date DESC LIMIT 1", con)
        as_of, index_price = str(idx["date"].iloc[0]), float(idx["index_price"].iloc[0])
    days = pd.bdate_range(end=pd.Timestamp(as_of), periods=DAYS)
    comp_cols, sent_cols = _cols(con, "daily_company_values", ("id",)), _cols(con, "sentiment", ("id",))
    # Seeded gap walk: log(price/blended) oscillates early, then converges to the anchor close.
    ok = (anchor["blended_value"].fillna(0) > 0) & (anchor["price"] > 0)
    intrinsic = anchor["blended_value"].where(ok, anchor["price"]).to_numpy()
    px0 = np.maximum(anchor["price"].to_numpy(), 1e-6)
    rng = np.random.default_rng(SEED)
    n = len(anchor)
    ramp = (np.arange(DAYS) / (DAYS - 1)).reshape(-1, 1)
    amp, phase, period = rng.uniform(0.02, 0.08, n), rng.uniform(0, 2 * np.pi, n), rng.uniform(5.0, 15.0, n)
    wiggle = amp * np.sin(2 * np.pi * np.arange(DAYS).reshape(-1, 1) / period + phase) + rng.normal(0, 0.012, (DAYS, n))
    prices = intrinsic * np.exp(np.log(px0 / intrinsic) * ramp + (1 - ramp) * wiggle)
    prices[-1] = px0  # converge exactly to the anchor close (no exp/log round-trip drift)
    w = anchor["index_weight"].to_numpy()
    wn = w / w.sum()
    idx_px = index_price * (prices / px0) @ wn  # cap-weighted returns rebuild the index level
    mcap, upside = anchor["market_cap"].to_numpy() * (prices / px0), intrinsic / prices - 1.0
    agg = lambda col: ((anchor[col].fillna(0).to_numpy() / prices) * wn).sum(axis=1) * idx_px  # mirrors index/aggregate_index_value.py
    iv, be, ba, bu = agg("blended_value"), agg("blended_bear_value"), agg("blended_base_value"), agg("blended_bull_value")
    idx_rows = [(d.date().isoformat(), *(float(x) for x in (idx_px[i], iv[i], iv[i] / idx_px[i], be[i] / idx_px[i], ba[i] / idx_px[i], bu[i] / idx_px[i], be[i], ba[i], bu[i], ok.mean(), mcap[i].sum()))) for i, d in enumerate(days)]
    consts = anchor[CONST_COLS].to_numpy()
    comp_rows, sent_rows = [], []
    for j, ticker in enumerate(anchor["ticker"]):
        for i, d in enumerate(days):
            day = d.date().isoformat()
            comp_rows.append((day, ticker, float(prices[i, j]), *consts[j, :6], float(upside[i, j]), consts[j, 6], consts[j, 7], consts[j, 8], float(mcap[i, j]), float(w[j]), *consts[j, 9:12]))
            s = deterministic_scores(ticker, d.date())
            sent_rows.append((day, ticker, s["analyst"], s["news"], s["options"], s["institutional"], s["overall"], day + " 12:00:00"))
    with con:
        for t in ("daily_company_values", "daily_index", "sentiment"): con.execute(f"DELETE FROM {t}")
        for t, cols, rws in (("daily_company_values", comp_cols, comp_rows), ("daily_index", _cols(con, "daily_index", ("id",)), idx_rows), ("sentiment", sent_cols, sent_rows)):
            con.executemany(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})", rws)
    con.close()
    print(f"generate_history: {DAYS} days | {len(comp_rows)} company rows | {len(sent_rows)} sentiment rows -> {config.DATABASE_PATH}")

if __name__ == "__main__":
    build_history()
