from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import date

from app.db.database import get_db
from app.models.booking import Booking
from app.core.security import get_current_user, get_current_admin

router = APIRouter(tags=["Веб-сторінки"])

templates = Jinja2Templates(directory="app/templates")

@router.get("/", include_in_schema=False)
async def root_redirect(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.cookies.get("access_token")

    if token:
        try:
            get_current_user(request=request, token=token, db=db)
            return RedirectResponse(url="/dashboard", status_code=302)
        except Exception:
            pass

    return RedirectResponse(url="/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Головна сторінка користувача"""
    
    active_bookings = db.query(Booking).options(
        joinedload(Booking.machine)
    ).filter(
        Booking.user_id == current_user.id,
        Booking.date >= date.today()
    ).order_by(Booking.date.asc()).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": current_user,
        "bookings": active_bookings
    })

@router.get("/booking", response_class=HTMLResponse)
async def booking_page(request: Request, current_user = Depends(get_current_user)):
    """Сторінка створення нового бронювання"""
    return templates.TemplateResponse("booking.html", {
        "request": request, 
        "user": current_user
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Сторінка входу в систему"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, current_user = Depends(get_current_admin)):
    """Адмін панель"""
    return templates.TemplateResponse("admin.html", {"request": request, "user": current_user})


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, current_user = Depends(get_current_admin)):
    """Сторінка управління користувачами"""
    return templates.TemplateResponse("admin_users.html", {"request": request, "user": current_user})


@router.get("/admin/bookings", response_class=HTMLResponse)
async def admin_bookings_page(request: Request, current_user = Depends(get_current_admin)):
    """Сторінка управління бронюваннями"""
    return templates.TemplateResponse("admin_bookings.html", {"request": request, "user": current_user})


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Сторінка поповнення балансу"""
    try:
        current_user = get_current_user(request=request, token=request.cookies.get("access_token"), db=next(get_db()))
        return templates.TemplateResponse("pricing.html", {"request": request, "user": current_user})
    except:
        return templates.TemplateResponse("pricing.html", {"request": request, "user": None})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Сторінка реєстрації"""
    return templates.TemplateResponse("register.html", {"request": request})