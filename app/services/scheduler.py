from apscheduler.schedulers.blocking import BlockingScheduler

from app.ingestion.instruments import ALL_TRACKED_INSTRUMENTS, SUPPORTED_TIMEFRAMES


def build_scheduler(backfill_fn):
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    for symbol in ALL_TRACKED_INSTRUMENTS:
        for tf in SUPPORTED_TIMEFRAMES:
            scheduler.add_job(
                backfill_fn,
                "cron",
                minute="*/5",
                kwargs={"symbol": symbol, "timeframe": tf, "years": 20},
                id=f"refresh::{symbol}::{tf}",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
    return scheduler
