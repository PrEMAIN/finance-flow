from flask import Blueprint, request, jsonify

from backend.extensions import db
from backend.models import User
from backend.auth_utils import hash_password, check_password, create_token, login_required
from backend.utils import sanitize_text, validate_email

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = sanitize_text(data.get("name") or "", 120)

    if not validate_email(email):
        return jsonify({"error": "Некорректный email"}), 400
    if len(password) < 6:
        return jsonify({"error": "Пароль должен содержать минимум 6 символов"}), 400
    if not name:
        return jsonify({"error": "Укажите имя"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Пользователь с таким email уже существует"}), 409

    user = User(email=email, password_hash=hash_password(password), name=name)
    db.session.add(user)
    db.session.commit()

    token = create_token(user.id)
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password(password, user.password_hash):
        return jsonify({"error": "Неверный email или пароль"}), 401

    token = create_token(user.id)
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@login_required
def me(user):
    return jsonify(user.to_dict())
