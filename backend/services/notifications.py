from backend.extensions import db
from backend.models import Notification


def create_notification(user_id: str, title: str, message: str, ntype: str = "info"):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=ntype,
    )
    db.session.add(notification)
    return notification


def check_budget_limit_notification(user, limit, spent: float):
    amount = float(limit.amount)
    if amount <= 0:
        return
    progress = spent / amount
    if progress >= 1:
        create_notification(
            user.id,
            "Лимит превышен",
            f"Расходы по категории «{limit.category.name}» превысили лимит ({spent:.2f} / {amount:.2f} ₽)",
            "warning",
        )
    elif progress >= 0.9:
        create_notification(
            user.id,
            "Лимит почти исчерпан",
            f"Использовано {progress * 100:.0f}% лимита по категории «{limit.category.name}»",
            "warning",
        )
