from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from db.models import DbShow, DbUserPrefs


class DbShowRepository(SQLAlchemyAsyncRepository[DbShow]):
    model_type = DbShow


class DbUserPrefsRepository(SQLAlchemyAsyncRepository[DbUserPrefs]):
    model_type = DbUserPrefs
    id_attribute = "user_id"
