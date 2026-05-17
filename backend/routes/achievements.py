from flask import Blueprint, jsonify

from backend.auth_utils import login_required
from backend.services.achievements import list_user_achievements, check_achievements

achievements_bp = Blueprint("achievements", __name__)


@achievements_bp.get("")
@login_required
def list_achievements(user):
    check_achievements(user)
    from backend.extensions import db
    db.session.commit()
    return jsonify(list_user_achievements(user))
