from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.services import payment_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payments",
    tags=["Оплати та Webhooks"]
)

@router.post("/webhook/monobank", status_code=status.HTTP_200_OK)
async def monobank_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Приймає автоматичні сповіщення (вебхуки) від Monobank про нові транзакції.
    Автоматично знаходить користувача за коментарем і нараховує прання.
    """
    try:
        webhook_data = await request.json()
        
        result = payment_service.process_monobank_webhook(db=db, webhook_data=webhook_data)
        
        logger.info(f"Обробка вебхуку Монобанк: {result}")
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Помилка обробки вебхуку: {e}")
        return {"status": "error_logged"}