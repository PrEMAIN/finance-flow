from flask import Blueprint, request, jsonify

from backend.auth_utils import login_required
from backend.services.stats import get_balance_summary, get_expense_chart

statistics_bp = Blueprint("statistics", __name__)


@statistics_bp.get("/summary")
@login_required
def summary(user):
    period = request.args.get("period", "month")
    if period not in ("day", "week", "month"):
        period = "month"
    return jsonify(get_balance_summary(user.id, period))


@statistics_bp.get("/chart")
@login_required
def chart(user):
    period = request.args.get("period", "month")
    if period not in ("day", "week", "month"):
        period = "month"
    return jsonify(get_expense_chart(user.id, period))
