from datetime import date

from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models import BudgetLimit, Category
from backend.auth_utils import login_required
from backend.utils import parse_amount
from backend.services.budget import enrich_limit
from backend.services.achievements import check_achievements
from sqlalchemy import or_

budget_bp = Blueprint("budget_limits", __name__)


@budget_bp.get("")
@login_required
def list_limits(user):
    limits = BudgetLimit.query.filter_by(user_id=user.id).all()
    return jsonify([enrich_limit(limit) for limit in limits])


@budget_bp.post("")
@login_required
def create_limit(user):
    data = request.get_json(silent=True) or {}
    amount = parse_amount(data.get("amount"))
    category_id = data.get("categoryId")
    start_date_str = data.get("startDate")

    if not amount:
        return jsonify({"error": "Укажите корректный лимит"}), 400

    category = Category.query.filter(
        Category.id == category_id,
        or_(Category.user_id.is_(None), Category.user_id == user.id),
    ).first()
    if not category:
        return jsonify({"error": "Категория не найдена"}), 404

    start_date = date.today().replace(day=1)
    if start_date_str:
        start_date = date.fromisoformat(start_date_str)

    existing = BudgetLimit.query.filter_by(
        user_id=user.id, category_id=category.id, start_date=start_date
    ).first()
    if existing:
        existing.amount = amount
        db.session.commit()
        check_achievements(user)
        db.session.commit()
        return jsonify(enrich_limit(existing))

    limit = BudgetLimit(
        user_id=user.id,
        category_id=category.id,
        amount=amount,
        start_date=start_date,
    )
    db.session.add(limit)
    db.session.commit()
    check_achievements(user)
    db.session.commit()
    return jsonify(enrich_limit(limit)), 201


@budget_bp.delete("/<limit_id>")
@login_required
def delete_limit(user, limit_id):
    limit = BudgetLimit.query.filter_by(id=limit_id, user_id=user.id).first()
    if not limit:
        return jsonify({"error": "Лимит не найден"}), 404
    db.session.delete(limit)
    db.session.commit()
    return jsonify({"message": "Лимит удалён"})
