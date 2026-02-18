from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from db.models import DbShow


class DbShowRepository(SQLAlchemyAsyncRepository[DbShow]):
    model_type = DbShow
