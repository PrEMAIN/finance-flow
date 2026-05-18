from sqlalchemy import func

from backend.extensions import db
from backend.models import (
    Achievement,
    UserAchievement,
    Transaction,
    BudgetLimit,
    Goal,
    Notification,
)


def _unlock(user, achievement: Achievement):
    exists = UserAchievement.query.filter_by(
        user_id=user.id, achievement_id=achievement.id
    ).first()
    if exists:
        return None
    record = UserAchievement(user_id=user.id, achievement_id=achievement.id)
    db.session.add(record)
    db.session.add(
        Notification(
            user_id=user.id,
            title="Новое достижение!",
            message=f"Вы получили достижение «{achievement.name}»",
            type="achievement",
        )
    )
    return achievement


def check_achievements(user):
    achievements = {a.code: a for a in Achievement.query.all()}
    unlocked = []

    tx_count = Transaction.query.filter_by(user_id=user.id).count()
    if tx_count >= 1 and "first_transaction" in achievements:
        result = _unlock(user, achievements["first_transaction"])
        if result:
            unlocked.append(result)
    if tx_count >= 10 and "ten_transactions" in achievements:
        result = _unlock(user, achievements["ten_transactions"])
        if result:
            unlocked.append(result)

    if (
        Transaction.query.filter_by(user_id=user.id, type="income").count() >= 1
        and "first_income" in achievements
    ):
        result = _unlock(user, achievements["first_income"])
        if result:
            unlocked.append(result)

    if BudgetLimit.query.filter_by(user_id=user.id).count() >= 1 and "first_limit" in achievements:
        result = _unlock(user, achievements["first_limit"])
        if result:
            unlocked.append(result)

    if Goal.query.filter_by(user_id=user.id).count() >= 1 and "first_goal" in achievements:
        result = _unlock(user, achievements["first_goal"])
        if result:
            unlocked.append(result)

    total_saved = (
        db.session.query(func.coalesce(func.sum(Goal.current_amount), 0))
        .filter(Goal.user_id == user.id)
        .scalar()
    )
    if float(total_saved or 0) >= 10000 and "saver" in achievements:
        result = _unlock(user, achievements["saver"])
        if result:
            unlocked.append(result)

    return unlocked


def list_user_achievements(user):
    unlocked_ids = {
        ua.achievement_id: ua.unlocked_at
        for ua in UserAchievement.query.filter_by(user_id=user.id).all()
    }
    return [
        a.to_dict(
            unlocked=a.id in unlocked_ids,
            unlocked_at=unlocked_ids.get(a.id),
        )
        for a in Achievement.query.order_by(Achievement.name).all()
    ]
