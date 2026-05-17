import html
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


EMAIL_RE = re.compile(r"^[\w.\-]+@[\w.\-]+\.\w+$")


def sanitize_text(value: str, max_len: int = 500) -> str:
    if not value:
        return ""
    cleaned = html.escape(value.strip())
    return cleaned[:max_len]


def parse_amount(value) -> Decimal | None:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
        if amount <= 0:
            return None
        return amount
    except (InvalidOperation, TypeError):
        return None


def parse_date(value, default=None):
    if not value:
        return default or datetime.utcnow()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return default or datetime.utcnow()


def validate_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email))
