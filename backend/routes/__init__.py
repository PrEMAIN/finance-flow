from backend.routes.auth import auth_bp
from backend.routes.transactions import transactions_bp
from backend.routes.categories import categories_bp
from backend.routes.budget_limits import budget_bp
from backend.routes.goals import goals_bp
from backend.routes.achievements import achievements_bp
from backend.routes.notifications import notifications_bp
from backend.routes.statistics import statistics_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(budget_bp, url_prefix="/api/budget-limits")
    app.register_blueprint(goals_bp, url_prefix="/api/goals")
    app.register_blueprint(achievements_bp, url_prefix="/api/achievements")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(statistics_bp, url_prefix="/api/statistics")
