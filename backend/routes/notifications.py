from flask import Blueprint, jsonify

from backend.extensions import db
from backend.models import Notification
from backend.auth_utils import login_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@login_required
def list_notifications(user):
    notifications = (
        Notification.query.filter_by(user_id=user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({"items": [n.to_dict() for n in notifications], "unreadCount": unread})


@notifications_bp.put("/<notification_id>/read")
@login_required
def mark_read(user, notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, user_id=user.id
    ).first()
    if not notification:
        return jsonify({"error": "Уведомление не найдено"}), 404
    notification.is_read = True
    db.session.commit()
    return jsonify(notification.to_dict())


@notifications_bp.put("/read-all")
@login_required
def mark_all_read(user):
    Notification.query.filter_by(user_id=user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return jsonify({"message": "Все уведомления прочитаны"})
