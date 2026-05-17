import uuid
from datetime import datetime, timezone

from backend.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    transactions = db.relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories = db.relationship("Category", back_populates="user", cascade="all, delete-orphan")
    budget_limits = db.relationship("BudgetLimit", back_populates="user", cascade="all, delete-orphan")
    goals = db.relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    achievements = db.relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "createdAt": self.created_at.isoformat(),
        }


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(16), default="📁")
    color = db.Column(db.String(7), default="#1B86C4")
    is_custom = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", back_populates="categories")
    transactions = db.relationship("Transaction", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
            "isCustom": self.is_custom,
            "userId": self.user_id,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # income | expense
    category_id = db.Column(db.String(36), db.ForeignKey("categories.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    comment = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="transactions")
    category = db.relationship("Category", back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "amount": float(self.amount),
            "type": self.type,
            "categoryId": self.category_id,
            "category": self.category.to_dict() if self.category else None,
            "date": self.date.isoformat(),
            "comment": self.comment or "",
            "createdAt": self.created_at.isoformat(),
        }


class BudgetLimit(db.Model):
    __tablename__ = "budget_limits"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    category_id = db.Column(db.String(36), db.ForeignKey("categories.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    period = db.Column(db.String(10), default="month", nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="budget_limits")
    category = db.relationship("Category")

    def to_dict(self, spent=0.0):
        limit_amount = float(self.amount)
        progress = spent / limit_amount if limit_amount > 0 else 0
        is_exceeded = spent > limit_amount
        return {
            "id": self.id,
            "userId": self.user_id,
            "categoryId": self.category_id,
            "category": self.category.to_dict() if self.category else None,
            "amount": limit_amount,
            "period": self.period,
            "startDate": self.start_date.isoformat(),
            "spent": round(spent, 2),
            "progress": round(progress, 4),
            "isExceeded": is_exceeded,
            "status": "exceeded" if is_exceeded else ("warning" if progress >= 0.9 else "ok"),
        }


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_amount = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    description = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="goals")

    def to_dict(self):
        target = float(self.target_amount)
        current = float(self.current_amount)
        progress = (current / target * 100) if target > 0 else 0
        return {
            "id": self.id,
            "userId": self.user_id,
            "targetAmount": target,
            "currentAmount": current,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "description": self.description,
            "progressPercent": round(min(progress, 100), 2),
            "createdAt": self.created_at.isoformat(),
        }


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(16), default="🏆")

    def to_dict(self, unlocked=False, unlocked_at=None):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "unlocked": unlocked,
            "unlockedAt": unlocked_at.isoformat() if unlocked_at else None,
        }


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = db.Column(db.String(36), db.ForeignKey("achievements.id"), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="achievements")
    achievement = db.relationship("Achievement")

    __table_args__ = (db.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), default="info", nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "isRead": self.is_read,
            "createdAt": self.created_at.isoformat(),
        }
