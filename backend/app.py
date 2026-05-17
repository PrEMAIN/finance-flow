import os, jwt, bcrypt, csv, io
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from models import db, User, Category, Transaction, BudgetLimit, Goal, Achievement, Notification
from marshmallow import Schema, fields, validate, ValidationError

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/finance.db'
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'super_secret_dev_key_2026')
db.init_app(app)

# --- Marshmallow Schemas (Валидация из ТЗ 4.1.2) ---
class UserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    name = fields.Str(required=True, validate=validate.Length(min=2))

class TxSchema(Schema):
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    type = fields.Str(required=True, validate=validate.OneOf(['income', 'expense']))
    category_id = fields.UUID(required=True)
    date = fields.Date(required=False)
    comment = fields.Str(required=False, validate=validate.Length(max=255))

user_schema = UserSchema()
tx_schema = TxSchema()

# --- Auth Middleware ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token: return jsonify({'error': 'Token missing'}), 401
        try:
            data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = db.session.get(User, data['user_id'])
            if not current_user: return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError: return jsonify({'error': 'Token expired'}), 401
        except: return jsonify({'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# --- Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    try: user_schema.load(data)
    except ValidationError as err: return jsonify(err.messages), 400
    if User.query.filter_by(email=data['email']).first(): return jsonify({'error': 'Email exists'}), 409
    hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    new_user = User(email=data['email'], password_hash=hashed, name=data['name'])
    db.session.add(new_user); db.session.commit()
    return jsonify({'message': 'Registered'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if not user or not bcrypt.checkpw(data['password'].encode(), user.password_hash.encode()):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = jwt.encode({'user_id': user.id, 'exp': datetime.utcnow() + timedelta(days=1)}, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token, 'name': user.name})

@app.route('/api/transactions', methods=['GET'])
@token_required
def get_tx(user):
    txs = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
    return jsonify([{'id': t.id, 'amount': t.amount, 'type': t.type, 'category': t.category.name, 
                     'date': t.date.isoformat(), 'comment': t.comment} for t in txs])

@app.route('/api/transactions', methods=['POST'])
@token_required
def add_tx(user):
    data = request.json
    try: tx_schema.load(data)
    except ValidationError as err: return jsonify(err.messages), 400
    
    new_tx = Transaction(user_id=user.id, **data)
    db.session.add(new_tx); db.session.commit()

    # Логика лимитов и уведомлений (ТЗ 4.1.4)
    if data['type'] == 'expense':
        limit = BudgetLimit.query.filter_by(user_id=user.id, category_id=data['category_id'], 
                                           month_year=datetime.utcnow().strftime('%Y-%m')).first()
        if limit:
            spent = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=user.id, category_id=data['category_id'], 
                                        type='expense').filter(Transaction.date >= datetime(limit.month_year + '-01').date()).scalar() or 0
            ratio = spent / limit.amount
            limit.is_exceeded = ratio >= 1.0
            db.session.commit()
            if ratio >= 0.9:
                db.session.add(Notification(user_id=user.id, title='Лимит', 
                                           message='Расход по категории приближается/превышен!', type='warning'))
                db.session.commit()

    # Проверка достижений (упрощённая)
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter_by(user_id=user.id, type='income').scalar() or 0
    if total_income >= 100000 and not Achievement.query.filter_by(name='Первый миллион').first():
        # В реальном проекте: связь user_achievements. Здесь упрощено для академической сдачи
        db.session.add(Notification(user_id=user.id, title='Достижение', 
                                   message='Вы накопили 100 000 ₽!', type='achievement'))
        db.session.commit()

    return jsonify({'message': 'Transaction saved'}), 201

@app.route('/api/stats/monthly', methods=['GET'])
@token_required
def get_stats(user):
    # Группировка по категориям за текущий месяц
    month = datetime.utcnow().strftime('%Y-%m-01')
    res = db.session.query(Category.name, db.func.sum(Transaction.amount))\
        .join(Transaction).filter(Transaction.user_id == user.id, Transaction.type == 'expense',
                                  Transaction.date >= datetime(month).date())\
        .group_by(Category.name).all()
    return jsonify(dict(res))

@app.route('/api/export/csv', methods=['GET'])
@token_required
def export_csv(user):
    txs = Transaction.query.filter_by(user_id=user.id).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Дата', 'Тип', 'Сумма', 'Категория', 'Комментарий'])
    for t in txs: cw.writerow([t.date, t.type, t.amount, t.category.name, t.comment])
    output = io.BytesIO(si.getvalue().encode('utf-8-sig'))
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='finance_report.csv')

# Serve Frontend
@app.route('/')
def index(): return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed categories
        if not Category.query.first():
            for c in [('Еда', '🍔', '#FF6B6B'), ('Транспорт', '🚌', '#4ECDC4'), ('Жилье', '🏠', '#FFE66D')]:
                db.session.add(Category(name=c[0], icon=c[1], color=c[2]))
            db.session.commit()
    app.run(debug=True, port=5000)