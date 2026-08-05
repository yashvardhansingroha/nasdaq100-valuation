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
├── valuation/     # DCF, multiples, blended, confidence (fundamentals only)
├── market/        # Sentiment modules (isolated from valuation)
├── index/         # Constituents, aggregation, sector analysis
├── database/      # SQLAlchemy ORM + SQLite history
├── dashboard/     # Streamlit UI
├── reports/       # Daily CSV/Excel/PDF output
├── scheduler/     # Automated daily runs
└── tests/         # pytest unit tests
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

## License

Private research tool — not financial advice.
