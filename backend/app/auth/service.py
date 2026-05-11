from datetime import date, datetime, timezone

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.billing.models import CreditBalance
from app.core.errors import EmailAlreadyExistsError


def _next_month_first_day() -> date:
    today = datetime.now(timezone.utc).date()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


async def register_user(db: AsyncSession, email: str, password: str) -> User:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(email=email.strip().lower(), password_hash=password_hash)

    try:
        async with db.begin():
            db.add(user)
            await db.flush()  # materialise user.id within the transaction

            balance = CreditBalance(
                user_id=user.id,
                credits_used=0,
                monthly_limit=1000,
                tier="free",
                reset_date=_next_month_first_day(),
            )
            db.add(balance)
    except IntegrityError as e:
        if e.orig and "email" in str(e.orig).lower():
            raise EmailAlreadyExistsError()
        raise

    return user
