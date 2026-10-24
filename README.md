# NASDAQ-100 Intrinsic Value & Market Intelligence Platform

Quantitative equity research platform that estimates the intrinsic value of the NASDAQ-100 by valuing every constituent individually (DCF + multiples, bear/base/bull), aggregating to an index fair-value ratio, and tracking 60 days of price-vs-intrinsic history and deterministic sentiment.

**Core principle: Intrinsic Value ≠ Market Sentiment** — valuation uses only fundamentals; sentiment is reported separately and never feeds valuation.

## Quick Start

```bash
pip install -r requirements.txt
copy .env.example .env          # optional API keys (works fully offline without them)

python generate_history.py      # deterministic 60-trading-day backfill -> database/history.db
streamlit run app.py            # 4-tab valuation dashboard (self-bootstraps the DB if missing)
python main.py --mode full      # live pipeline: constituents -> valuation -> sentiment -> DB -> reports
pytest -q                       # 23 unit tests
```

## The Dashboard (`app.py`)

| Tab | What it shows |
|-----|---------------|
| Index Overview & Fair-Value Gap | NDX level vs intrinsic value, fair-value ratio, widest per-name gaps |
| DCF Bear/Base/Bull vs Multiples | Per-ticker price vs scenario DCF / multiples / blended estimates |
| Sector Attribution | Each sector's weight × (blended/price − 1) contribution to the index gap |
| 60-Day Historical Trend & Sentiment | Index price vs intrinsic band, fair-value ratio, sentiment overlay |

Every metric is computed at runtime from `database/history.db` — no hardcoded numbers. If the DB is missing, `app.py` runs `generate_history.py` automatically.

## Pipeline Components

- **`valuation/`** — FCF DCF with bear/base/bull scenarios, sector-median multiples (P/E, P/S, EV/EBITDA), 50/50 blend, 0-100 confidence score (fundamentals only)
- **`market/`** — sentiment engine: analyst / news / options / institutional pillars, all deterministic scores in [-1, +1] (seeded per ticker-day, no live-API randomness), weighted overall
- **`index/`** — constituent fetching (Wikipedia + fallback), cap-weighted aggregation to index intrinsic value, sector/contribution analysis
- **`database/`** — append-only SQLite history (`daily_company_values`, `daily_index`, `sentiment`) via SQLAlchemy
- **`generate_history.py`** — seeded 60-trading-day backfill: market prices take a mean-reverting gap walk around intrinsic values and converge exactly to the real anchor close; fundamentals stay at the anchor snapshot; idempotent (same output every run)
- **`reports/`** — daily CSV/XLSX/PDF snapshots
- **`scheduler/`** + `run_daily.bat` — Windows Task Scheduler daily runs
- **`dashboard/dashboard.py`** — legacy multipage UI (superseded by `app.py`)

## CLI Modes (`python main.py --mode ...`)

| Mode | Description |
|------|-------------|
| `full` | Valuation + sentiment + reports |
| `valuation` | Valuation only |
| `constituents` | Refresh constituent/weights cache |
| `sentiment` | Deterministic sentiment only |

## Project Structure

```
nasdaq100-valuation/
├── app.py             # 4-tab Streamlit dashboard (self-bootstrapping)
├── generate_history.py# Deterministic 60-day history backfill
├── main.py            # CLI pipeline entry point
├── valuation/         # DCF, multiples, blended, confidence
├── market/            # Deterministic sentiment (isolated from valuation)
├── index/             # Constituents, aggregation, sector analysis
├── database/          # SQLAlchemy ORM + SQLite history
├── utils/             # Data provider, models, logging, history queries
├── reports/           # Daily CSV/XLSX/PDF output
├── scheduler/         # Automated daily runs
└── tests/             # pytest unit tests (23)
```

## Configuration

All assumptions live in `config.py`: discount rate (10%), terminal growth (2.5%), projection years (5), blend weights, scenario probabilities (20/60/20), sentiment weights, cache TTLs, DB/report paths. API keys are optional via `.env` — the platform runs fully offline from cached fundamentals.

## Reproducibility

Fixed seeds everywhere: `generate_history.py` (numpy seed 20260809) and the sentiment engine (per-pillar/per-ticker/per-day `random.Random` seeds) make every number reproducible. Re-running the generator is bit-identical (verified).

## License

Private research tool — not financial advice.
