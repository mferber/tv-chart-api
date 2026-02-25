from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from litestar_users_setup.models import User

test_users = {
    "test_user1": ("testuser1@example.com", "password1"),
    "test_user2": ("testuser2@example.com", "password2"),
}


def get_user_info(tag: str) -> tuple[str, str]:
    try:
        return test_users[tag]
    except KeyError:
        raise KeyError(f"Test user '{tag}' not found")


async def get_user_id(tag: str, db_session: AsyncSession) -> UUID:
    user_email = get_user_info(tag)[0]
    q = select(User.id).filter_by(email=user_email)
    result: UUID | None = await db_session.scalar(q)
    if result is None:
        raise KeyError(f"Test user email '{user_email}' not in db")
    return result
