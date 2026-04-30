import uuid

import pytest

from db.models import DbUserPrefs
from models.prefs import UserPrefs


def test_db_prefs_model_to_domain_model_conversion() -> None:
    sut = DbUserPrefs()
    sut.show_favorites_only = True

    domain_model = sut.to_user_prefs_model()

    assert domain_model.show_favorites_only


@pytest.mark.asyncio
async def test_domain_prefs_model_to_db_model_conversion() -> None:
    domain_model = UserPrefs(show_favorites_only=True)
    user_id = uuid.uuid4()

    sut = DbUserPrefs.from_user_prefs_model(domain_model, owner_id=user_id)

    assert sut.show_favorites_only
    assert sut.user_id == user_id
