import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(scope="session", autouse=True)
def db_engine():
    from app.auth.models import User  # noqa: F401 - register with Base
    from app.billing.models import CreditBalance  # noqa: F401 - register with Base
    from app.core.config import settings
    from app.db.base import Base

    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_db(db_engine):
    yield
    with db_engine.begin() as conn:
        conn.execute(text("DELETE FROM credit_balances"))
        conn.execute(text("DELETE FROM users"))
