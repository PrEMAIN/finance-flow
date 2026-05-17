from datetime import date

from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models import Goal
from backend.auth_utils import login_required
from backend.utils import parse_amount, sanitize_text
from backend.services.achievements import check_achievements

goals_bp = Blueprint("goals", __name__)


@goals_bp.get("")
@login_required
def list_goals(user):
    goals = Goal.query.filter_by(user_id=user.id).order_by(Goal.created_at.desc()).all()
    return jsonify([g.to_dict() for g in goals])


@goals_bp.post("")
@login_required
def create_goal(user):
    data = request.get_json(silent=True) or {}
    target = parse_amount(data.get("targetAmount"))
    description = sanitize_text(data.get("description") or "", 255)
    deadline_str = data.get("deadline")

    if not target:
        return jsonify({"error": "Укажите целевую сумму"}), 400
    if not description:
        return jsonify({"error": "Укажите описание цели"}), 400

    deadline = date.fromisoformat(deadline_str) if deadline_str else None
    goal = Goal(
        user_id=user.id,
        target_amount=target,
        current_amount=0,
        deadline=deadline,
        description=description,
    )
    db.session.add(goal)
    db.session.commit()
    check_achievements(user)
    db.session.commit()
    return jsonify(goal.to_dict()), 201


@goals_bp.post("/<goal_id>/contribute")
@login_required
def contribute(user, goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=user.id).first()
    if not goal:
        return jsonify({"error": "Цель не найдена"}), 404

    data = request.get_json(silent=True) or {}
    amount = parse_amount(data.get("amount"))
    if not amount:
        return jsonify({"error": "Укажите корректную сумму"}), 400

    goal.current_amount = float(goal.current_amount) + float(amount)
    db.session.commit()
    check_achievements(user)
    db.session.commit()
    return jsonify(goal.to_dict())


@goals_bp.delete("/<goal_id>")
@login_required
def delete_goal(user, goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=user.id).first()
    if not goal:
        return jsonify({"error": "Цель не найдена"}), 404
    db.session.delete(goal)
    db.session.commit()
    return jsonify({"message": "Цель удалена"})
