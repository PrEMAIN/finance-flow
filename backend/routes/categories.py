from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from backend.extensions import db
from backend.models import Category, Transaction
from backend.auth_utils import login_required
from backend.utils import sanitize_text
from backend.services.achievements import check_achievements

categories_bp = Blueprint("categories", __name__)


@categories_bp.get("")
@login_required
def list_categories(user):
    categories = (
        Category.query.filter(
            or_(Category.user_id.is_(None), Category.user_id == user.id)
        )
        .order_by(Category.is_custom, Category.name)
        .all()
    )
    return jsonify([c.to_dict() for c in categories])


@categories_bp.post("")
@login_required
def create_category(user):
    data = request.get_json(silent=True) or {}
    name = sanitize_text(data.get("name") or "", 100)
    icon = sanitize_text(data.get("icon") or "📁", 16)
    color = sanitize_text(data.get("color") or "#1B86C4", 7)

    if not name:
        return jsonify({"error": "Укажите название категории"}), 400

    exists = Category.query.filter(
        Category.user_id == user.id, Category.name == name
    ).first()
    if exists:
        return jsonify({"error": "Категория с таким названием уже существует"}), 409

    category = Category(
        name=name, icon=icon, color=color, is_custom=True, user_id=user.id
    )
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@categories_bp.put("/<category_id>")
@login_required
def update_category(user, category_id):
    category = Category.query.filter_by(id=category_id, user_id=user.id).first()
    if not category or not category.is_custom:
        return jsonify({"error": "Категория не найдена или недоступна для редактирования"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        category.name = sanitize_text(data["name"], 100)
    if "icon" in data:
        category.icon = sanitize_text(data["icon"], 16)
    if "color" in data:
        category.color = sanitize_text(data["color"], 7)

    db.session.commit()
    return jsonify(category.to_dict())


@categories_bp.delete("/<category_id>")
@login_required
def delete_category(user, category_id):
    category = Category.query.filter_by(id=category_id, user_id=user.id).first()
    if not category or not category.is_custom:
        return jsonify({"error": "Категория не найдена"}), 404

    if Transaction.query.filter_by(category_id=category.id).first():
        return jsonify({"error": "Нельзя удалить категорию с транзакциями"}), 400

    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Категория удалена"})
