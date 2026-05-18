# Finance-flow

Веб-приложение для учёта личных финансов (проект по дисциплине «Системная и программная инженерия», РТУ МИРЭА).

## Возможности

- Регистрация и авторизация (JWT, bcrypt)
- Транзакции: доходы и расходы с категориями, фильтрацией и редактированием
- Бюджетные лимиты по категориям с визуальными индикаторами (90% — жёлтый, 100%+ — красный)
- Статистика и круговая диаграмма расходов (Chart.js)
- Экспорт транзакций в CSV
- Финансовые цели и отслеживание накоплений
- Достижения и уведомления
- Пользовательские категории

## Стек

| Уровень | Технологии |
|---------|------------|
| Frontend | HTML5, CSS3, JavaScript (ES6+), Chart.js |
| Backend | Python 3.10+, Flask, SQLAlchemy, PyJWT, bcrypt |
| БД | SQLite (разработка), PostgreSQL (продакшн) |

## Быстрый старт

```bash
# 1. Создать виртуальное окружение
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 2. Установить зависимости
pip install -r requirements.txt

# 3. (Опционально) Настроить переменные окружения
copy .env.example .env

# 4. Запустить приложение
python run.py
```

Откройте в браузере: **http://localhost:5000**

## Структура проекта

```
Finance-Flow/
├── backend/           # Flask API, модели, сервисы
├── frontend/          # Статические файлы UI
├── run.py             # Точка входа
├── requirements.txt
└── README.md
```

## API (основные эндпоинты)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход |
| GET | `/api/transactions` | Список транзакций |
| POST | `/api/transactions` | Создать транзакцию |
| GET | `/api/transactions/export` | Экспорт CSV |
| GET | `/api/statistics/summary` | Сводка за период |
| GET | `/api/statistics/chart` | Данные для диаграммы |
| GET/POST | `/api/budget-limits` | Лимиты бюджета |
| GET/POST | `/api/goals` | Финансовые цели |
| GET | `/api/achievements` | Достижения |
| GET | `/api/notifications` | Уведомления |

## Цветовая схема UI

- Фон: `#0A8F57`
- Текст: `#04040F`
- Акцент: `#1B86C4`

## Команда

- Агарков Р.А. — руководитель проекта, тестирование
- Герич Б.М. — аналитик, backend
- Коновалов И.Д. — дизайн, frontend
