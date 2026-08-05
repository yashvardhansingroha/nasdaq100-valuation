"""Daily scheduler for automated pipeline runs."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import schedule

import config
from utils.logging_config import setup_logging

logger = setup_logging(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_pipeline(mode: str = "full") -> None:
    """Execute the main pipeline as a subprocess."""
    cmd = [sys.executable, str(PROJECT_ROOT / "main.py"), "--mode", mode]
    logger.info("Scheduler starting pipeline: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=7200)
        if result.returncode == 0:
            logger.info("Pipeline completed successfully")
        else:
            logger.error("Pipeline failed (code %d): %s", result.returncode, result.stderr[-500:])
    except subprocess.TimeoutExpired:
        logger.error("Pipeline timed out after 2 hours")
    except Exception as exc:
        logger.error("Pipeline execution error: %s", exc)


def start_scheduler(mode: str = "full") -> None:
    """Start the daily scheduler loop."""
    run_time = config.SCHEDULE_TIME
    logger.info("Scheduler configured for daily run at %s", run_time)
    schedule.every().day.at(run_time).do(run_pipeline, mode=mode)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_scheduler()
