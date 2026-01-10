from advanced_alchemy.base import UUIDBase
from litestar_users.adapter.sqlalchemy.mixins import SQLAlchemyUserMixin


class User(UUIDBase, SQLAlchemyUserMixin):
    """SQLAlchemy mapped class for user records.

    Includes standard columns defined in SQLAlchemyUserMixin.
    """

    __tablename__ = "user_account"
