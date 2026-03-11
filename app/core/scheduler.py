from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.models.user import User
from app.db.database import SessionLocal
import logging

scheduler = None
logger = logging.getLogger(__name__)


def reset_monthly_washes():
    """Reset monthly wash usage counter for all users."""
    db = SessionLocal()
    try:
        updated_rows = db.query(User).update({User.washes_used_this_month: 0})
        db.commit()
        logger.info("Monthly washes reset completed. Updated users: %s", updated_rows)
    except Exception:
        db.rollback()
        logger.exception("Failed to reset monthly washes")
        raise
    finally:
        db.close()

def init_scheduler(engine):
    global scheduler
    jobstores = {
        'default': SQLAlchemyJobStore(engine=engine, tablename='apscheduler_jobs')
    }
    scheduler = AsyncIOScheduler(
        jobstores=jobstores, 
        timezone="Europe/Kyiv"
    )

    # APScheduler 3.x with Europe/Kyiv can skip April when the job is set to 00:00,
    # so run at 01:00 local time to avoid the DST edge case.
    scheduler.add_job(
        reset_monthly_washes,
        trigger='cron',
        day=1,
        hour=1,
        minute=0,
        id='monthly_washes_reset',
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600
    )

    return scheduler