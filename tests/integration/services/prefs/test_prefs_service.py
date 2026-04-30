import pytest
from helpers.testing_data.users import get_user_id
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories import DbUserPrefsRepository
from models.prefs import UserPrefs
from services.prefs_service import PrefsService


@pytest.mark.asyncio
async def test_get_user_prefs(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user2", sess)
    sut = PrefsService(db_session=autorollback_db_session, user_id=user_id)

    prefs = await sut.get_prefs()

    assert prefs.show_favorites_only


@pytest.mark.asyncio
async def test_update_user_prefs(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user2", sess)
    sut = PrefsService(db_session=autorollback_db_session, user_id=user_id)

    await sut.update_prefs(UserPrefs(show_favorites_only=False))

    prefs = await sut.get_prefs()

    assert not prefs.show_favorites_only


@pytest.mark.asyncio
async def test_get_user_prefs_lazy_initializes_missing_prefs(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    repo = DbUserPrefsRepository(session=sess)

    # delete the existing prefs to see if they get recreated on demand
    await repo.delete_where(auto_commit=True)

    user_id = await get_user_id("test_user2", sess)
    sut = PrefsService(db_session=autorollback_db_session, user_id=user_id)

    prefs = await sut.get_prefs()

    # default setting is False
    assert not prefs.show_favorites_only


@pytest.mark.asyncio
async def test_update_user_prefs_lazy_initializes_missing_prefs(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    repo = DbUserPrefsRepository(session=sess)

    # delete the existing prefs to see if they get recreated when we do the update
    await repo.delete_where(auto_commit=True)

    user_id = await get_user_id("test_user2", sess)
    sut = PrefsService(db_session=autorollback_db_session, user_id=user_id)

    await sut.update_prefs(UserPrefs(show_favorites_only=True))

    prefs = await sut.get_prefs()

    assert prefs.show_favorites_only
