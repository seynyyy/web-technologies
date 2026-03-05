from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
from app.routers import machines, auth, bookings, payments, admin, pages
from app.core import scheduler as scheduler_module
from app.core.scheduler import init_scheduler
from app.db.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    init_scheduler(engine)
    logger.info("🚀 Запуск планувальника завдань...")
    scheduler_module.scheduler.start()
    logger.info(f"✅ Scheduler запущений: running={scheduler_module.scheduler.running}")
    logger.info(f"📋 Поточна кількість завдань: {len(scheduler_module.scheduler.get_jobs())}")
    
    yield
    
    logger.info("🛑 Зупинка планувальника завдань...")
    scheduler_module.scheduler.shutdown()
    logger.info("✅ Scheduler зупинений")

app = FastAPI(title="Laundry API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(machines.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(pages.router)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 404:
        return HTMLResponse(
            content=templates.get_template("404.html").render(request=request),
            status_code=404
        )
    elif exc.status_code == 401:
        return HTMLResponse(
            content=templates.get_template("401.html").render(request=request),
            status_code=401
        )
    elif exc.status_code == 403:
        return HTMLResponse(
            content=templates.get_template("403.html").render(request=request),
            status_code=403
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )