import difflib
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.user import User


DEFAULT_PRICE = Decimal("50.00")
DISCOUNT_PRICE = Decimal("40.00")

def find_user_by_comment(db: Session, comment: str) -> User | None:
    """
    Шукає користувача за коментарем до платежу (зазвичай це ПІБ або логін).
    Використовує алгоритм нечіткого пошуку, як у вашому старому коді.
    """
    if not comment:
        return None
        
    comment_lower = comment.strip().lower()
    
    users = db.query(User).all()
    
    for user in users:
        if user.full_name and user.full_name.lower() == comment_lower:
            return user
            
    names_dict = {user.full_name.lower(): user for user in users if user.full_name}
    
    matches = difflib.get_close_matches(comment_lower, names_dict.keys(), n=1, cutoff=0.8)
    
    if matches:
        return names_dict[matches[0]]
        
    return None

def process_monobank_webhook(db: Session, webhook_data: dict):
    """
    Обробляє вхідний webhook від Monobank.
    """
    if webhook_data.get("type") != "StatementItem":
        return {"status": "ignored", "detail": "Не є транзакцією"}
        
    data = webhook_data.get("data", {}).get("statementItem", {})
    
    amount_kopecks = data.get("amount", 0)
    comment = data.get("description", "")
    
    if amount_kopecks <= 0:
        return {"status": "ignored", "detail": "Від'ємна або нульова сума"}
        
    amount_uah = Decimal(amount_kopecks) / 100
    
    user = find_user_by_comment(db, comment)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Користувача не розпізнано за коментарем"
        )
        
    price_per_wash = DISCOUNT_PRICE if user.has_discount else DEFAULT_PRICE
    washes_to_add = int(amount_uah // price_per_wash)
    
    if washes_to_add > 0:
        user.washes_left += washes_to_add
        db.commit()
        db.refresh(user)
        
    return {
        "status": "success", 
        "user_id": user.id, 
        "amount_uah": float(amount_uah), 
        "added_washes": washes_to_add
    }