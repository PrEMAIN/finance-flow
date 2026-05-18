from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func

from backend.extensions import db
from backend.models import Transaction, Category


def period_bounds(period: str):
    now = datetime.now(timezone.utc)
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


def get_balance_summary(user_id: str, period: str = "month"):
    start, end = period_bounds(period)
    rows = (
        db.session.query(Transaction.type, func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .group_by(Transaction.type)
        .all()
    )
    income = expense = 0.0
    for tx_type, total in rows:
        value = float(total or 0)
        if tx_type == "income":
            income = value
        else:
            expense = value
    return {
        "period": period,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(income - expense, 2),
    }


def get_expense_chart(user_id: str, period: str = "month"):
    start, end = period_bounds(period)
    rows = (
        db.session.query(
            Category.id,
            Category.name,
            Category.color,
            Category.icon,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .group_by(Category.id, Category.name, Category.color, Category.icon)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    total_expense = sum(float(r.total or 0) for r in rows)
    segments = []
    for row in rows:
        amount = float(row.total or 0)
        segments.append(
            {
                "categoryId": row.id,
                "name": row.name,
                "color": row.color,
                "icon": row.icon,
                "amount": round(amount, 2),
                "percent": round(amount / total_expense * 100, 1) if total_expense else 0,
            }
        )
    return {"totalExpense": round(total_expense, 2), "segments": segments}
