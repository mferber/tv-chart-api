from advanced_alchemy.base import UUIDAuditBase
from litestar_users.password import PasswordManager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer  # type: ignore

from setup.litestar_users.models import User

_EMAIL_1 = "testuser1@example.com"
_PASSWORD_1 = "password1"


def _add_user(db_session: Session, email: str, password: str) -> None:
    hashed_pw = PasswordManager().hash(password)
    db_session.add(
        User(
            email=email,
            password_hash=hashed_pw,
            is_active=True,
            is_verified=True,
        )
    )


def seed_test_db(test_db_container: PostgresContainer) -> None:
    engine = create_engine(test_db_container.get_connection_url())
    UUIDAuditBase.metadata.create_all(engine)

    with Session(engine) as db_session:
        _add_user(db_session, _EMAIL_1, _PASSWORD_1)
        db_session.commit()
