import httpx
import logging
from app.core.security import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


async def send_telegram_message(telegram_id: int, text: str) -> bool:
    """Відправка повідомлення через Telegram Bot API"""
    if not telegram_id:
        logger.warning("Cannot send notification: telegram_id is None")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                TELEGRAM_API_URL,
                json={
                    "chat_id": telegram_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Notification sent to telegram_id={telegram_id}")
                return True
            else:
                logger.error(f"Failed to send notification: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")
        return False


async def send_start_notification(telegram_id: int, machine_name: str):
    """Відправляється, коли настає час прання"""
    logger.info(f"🎯 START NOTIFICATION triggered for telegram_id={telegram_id}, machine={machine_name}")
    message = f"🧺 <b>Час прання почався!</b>\n\Пральна машина: <b>{machine_name}</b>\n\nПочався час для прання."
    result = await send_telegram_message(telegram_id, message)
    logger.info(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    return result


async def send_end_notification(telegram_id: int, machine_name: str):
    """Відправляється наприкінці прання"""
    logger.info(f"🎯 END NOTIFICATION triggered for telegram_id={telegram_id}, machine={machine_name}")
    message = f"✅ <b>Прання завершено!</b>\n\nПральна машина: <b>{machine_name}</b>\n\nБудь ласка, заберіть ваші речі протягом 15 хвилин."
    result = await send_telegram_message(telegram_id, message)
    logger.info(f"   Result: {'✅ Success' if result else '❌ Failed'}")
    return result