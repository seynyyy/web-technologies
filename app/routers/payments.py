from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.services import payment_service

# Налаштовуємо логування, щоб бачити платежі в консолі сервера
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payments",
    tags=["Оплати та Webhooks"]
)

@router.post("/webhook/monobank", status_code=status.HTTP_200_OK)
async def monobank_webhook(
    request: Request, # Використовуємо Request, щоб отримати сирий JSON
    db: Session = Depends(get_db)
):
    """
    Приймає автоматичні сповіщення (вебхуки) від Monobank про нові транзакції.
    Автоматично знаходить користувача за коментарем і нараховує прання.
    """
    try:
        # 1. Отримуємо дані від Монобанку асинхронно
        webhook_data = await request.json()
        
        # 2. Передаємо їх у наш сервіс, який ми написали раніше
        result = payment_service.process_monobank_webhook(db=db, webhook_data=webhook_data)
        
        # 3. Записуємо результат у логи сервера (дуже корисно для дебагу!)
        logger.info(f"Обробка вебхуку Монобанк: {result}")
        
        # Монобанк очікує отримати статус 200 OK
        return {"status": "received"}
        
    except Exception as e:
        # ВАЖЛИВО: Навіть якщо сталася помилка (наприклад, юзера не знайдено),
        # ми не повертаємо 404 або 500 самому Монобанку. 
        # Інакше Монобанк думатиме, що наш сервер впав, і буде слати цей платіж 
        # знову і знову протягом доби.
        logger.error(f"Помилка обробки вебхуку: {e}")
        return {"status": "error_logged"}