from dataclasses import dataclass

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from litestar.dto import DataclassDTO

from .models import User


@dataclass
class UserRegistrationSchema:
    email: str
    password: str


class UserRegistrationDTO(DataclassDTO[UserRegistrationSchema]):
    pass


class UserReadDTO(SQLAlchemyDTO[User]):
    config = SQLAlchemyDTOConfig(
        exclude={
            "password_hash",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        }
    )


class UserUpdateDTO(SQLAlchemyDTO[User]):
    config = SQLAlchemyDTOConfig(exclude={"password_hash"}, partial=True)
