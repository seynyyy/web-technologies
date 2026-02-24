from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = None

def init_scheduler(engine):
    global scheduler
    jobstores = {
        'default': SQLAlchemyJobStore(engine=engine, tablename='apscheduler_jobs')
    }
    scheduler = AsyncIOScheduler(
        jobstores=jobstores, 
        timezone="Europe/Kyiv"
    )
    return scheduler