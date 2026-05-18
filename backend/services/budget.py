from calendar import monthrange
from datetime import date
from decimal import Decimal

from sqlalchemy import func

from backend.extensions import db
from backend.models import Transaction, BudgetLimit


def month_range(for_date: date | None = None):
    today = for_date or date.today()
    start = today.replace(day=1)
    _, last_day = monthrange(today.year, today.month)
    end = today.replace(day=last_day)
    return start, end


def get_category_spent(user_id: str, category_id: str, start: date, end: date) -> float:
    total = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.type == "expense",
            func.date(Transaction.date) >= start,
            func.date(Transaction.date) <= end,
        )
        .scalar()
    )
    return float(total or 0)


def enrich_limit(limit: BudgetLimit) -> dict:
    start, end = month_range(limit.start_date)
    spent = get_category_spent(limit.user_id, limit.category_id, start, end)
    return limit.to_dict(spent=spent)
