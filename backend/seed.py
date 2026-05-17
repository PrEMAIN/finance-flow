from backend.extensions import db
from backend.models import Category, Achievement

DEFAULT_CATEGORIES = [
    ("Еда", "🍔", "#FF6B6B", False),
    ("Транспорт", "🚌", "#4ECDC4", False),
    ("Жильё", "🏠", "#45B7D1", False),
    ("Развлечения", "🎬", "#96CEB4", False),
    ("Здоровье", "💊", "#FFEAA7", False),
    ("Образование", "📚", "#DDA0DD", False),
    ("Зарплата", "💰", "#0A8F57", False),
    ("Прочее", "📁", "#1B86C4", False),
]

DEFAULT_ACHIEVEMENTS = [
    ("first_transaction", "Первый шаг", "Добавьте первую транзакцию", "🎯"),
    ("ten_transactions", "Активный учёт", "Добавьте 10 транзакций", "📊"),
    ("first_limit", "Бюджетник", "Установите первый лимит по категории", "🛡️"),
    ("first_goal", "Целеустремлённый", "Создайте первую финансовую цель", "🎯"),
    ("first_income", "Первый доход", "Зафиксируйте первый доход", "💵"),
    ("saver", "Накопитель", "Накопите 10 000 ₽ на цели", "🏦"),
    ("budget_master", "Мастер бюджета", "Не превышайте лимиты в течение месяца", "⭐"),
]


def seed_database():
    if Category.query.filter_by(is_custom=False, user_id=None).count() == 0:
        for name, icon, color, is_custom in DEFAULT_CATEGORIES:
            db.session.add(
                Category(name=name, icon=icon, color=color, is_custom=is_custom, user_id=None)
            )

    if Achievement.query.count() == 0:
        for code, name, description, icon in DEFAULT_ACHIEVEMENTS:
            db.session.add(
                Achievement(code=code, name=name, description=description, icon=icon)
            )

    db.session.commit()
