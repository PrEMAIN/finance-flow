import csv
import io
from datetime import datetime

from flask import Blueprint, request, jsonify, Response
from sqlalchemy import or_, and_

from backend.extensions import db
from backend.models import Transaction, Category, BudgetLimit
from backend.auth_utils import login_required
from backend.utils import sanitize_text, parse_amount, parse_date
from backend.services.budget import month_range, get_category_spent, enrich_limit
from backend.services.achievements import check_achievements
from backend.services.notifications import check_budget_limit_notification

transactions_bp = Blueprint("transactions", __name__)


def _get_category(user, category_id):
    return Category.query.filter(
        Category.id == category_id,
        or_(Category.user_id.is_(None), Category.user_id == user.id),
    ).first()


def _check_limits_after_expense(user, category_id):
    start, end = month_range()
    limits = BudgetLimit.query.filter_by(user_id=user.id, category_id=category_id).all()
    for limit in limits:
        if limit.start_date <= end:
            spent = get_category_spent(user.id, category_id, start, end)
            check_budget_limit_notification(user, limit, spent)


@transactions_bp.get("")
@login_required
def list_transactions(user):
    query = Transaction.query.filter_by(user_id=user.id)

    tx_type = request.args.get("type")
    category_id = request.args.get("categoryId")
    date_from = request.args.get("dateFrom")
    date_to = request.args.get("dateTo")
    amount_min = request.args.get("amountMin")
    amount_max = request.args.get("amountMax")

    if tx_type in ("income", "expense"):
        query = query.filter(Transaction.type == tx_type)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if date_from:
        query = query.filter(Transaction.date >= parse_date(date_from))
    if date_to:
        query = query.filter(Transaction.date <= parse_date(date_to))
    if amount_min:
        query = query.filter(Transaction.amount >= parse_amount(amount_min))
    if amount_max:
        query = query.filter(Transaction.amount <= parse_amount(amount_max))

    transactions = query.order_by(Transaction.date.desc()).all()
    return jsonify([t.to_dict() for t in transactions])


@transactions_bp.post("")
@login_required
def create_transaction(user):
    data = request.get_json(silent=True) or {}
    amount = parse_amount(data.get("amount"))
    tx_type = data.get("type")
    category_id = data.get("categoryId")
    comment = sanitize_text(data.get("comment") or "")
    tx_date = parse_date(data.get("date"))

    if not amount:
        return jsonify({"error": "Сумма должна быть положительным числом"}), 400
    if tx_type not in ("income", "expense"):
        return jsonify({"error": "Тип должен быть income или expense"}), 400

    category = _get_category(user, category_id)
    if not category:
        return jsonify({"error": "Категория не найдена"}), 404

    transaction = Transaction(
        user_id=user.id,
        amount=amount,
        type=tx_type,
        category_id=category.id,
        date=tx_date,
        comment=comment,
    )
    db.session.add(transaction)
    db.session.commit()

    if tx_type == "expense":
        _check_limits_after_expense(user, category.id)

    check_achievements(user)
    db.session.commit()

    return jsonify(transaction.to_dict()), 201


@transactions_bp.put("/<transaction_id>")
@login_required
def update_transaction(user, transaction_id):
    transaction = Transaction.query.filter_by(
        id=transaction_id, user_id=user.id
    ).first()
    if not transaction:
        return jsonify({"error": "Транзакция не найдена"}), 404

    data = request.get_json(silent=True) or {}
    if "amount" in data:
        amount = parse_amount(data["amount"])
        if not amount:
            return jsonify({"error": "Некорректная сумма"}), 400
        transaction.amount = amount
    if "type" in data and data["type"] in ("income", "expense"):
        transaction.type = data["type"]
    if "categoryId" in data:
        category = _get_category(user, data["categoryId"])
        if not category:
            return jsonify({"error": "Категория не найдена"}), 404
        transaction.category_id = category.id
    if "date" in data:
        transaction.date = parse_date(data["date"])
    if "comment" in data:
        transaction.comment = sanitize_text(data["comment"])

    db.session.commit()
    if transaction.type == "expense":
        _check_limits_after_expense(user, transaction.category_id)
    db.session.commit()
    return jsonify(transaction.to_dict())


@transactions_bp.delete("/<transaction_id>")
@login_required
def delete_transaction(user, transaction_id):
    transaction = Transaction.query.filter_by(
        id=transaction_id, user_id=user.id
    ).first()
    if not transaction:
        return jsonify({"error": "Транзакция не найдена"}), 404

    db.session.delete(transaction)
    db.session.commit()
    return jsonify({"message": "Транзакция удалена"})


@transactions_bp.get("/export")
@login_required
def export_csv(user):
    transactions = (
        Transaction.query.filter_by(user_id=user.id)
        .order_by(Transaction.date.desc())
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Дата", "Тип", "Категория", "Сумма", "Комментарий"])
    for tx in transactions:
        writer.writerow(
            [
                tx.date.strftime("%Y-%m-%d %H:%M"),
                "Доход" if tx.type == "income" else "Расход",
                tx.category.name if tx.category else "",
                f"{float(tx.amount):.2f}",
                tx.comment,
            ]
        )

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=finance_flow_report.csv"},
    )
