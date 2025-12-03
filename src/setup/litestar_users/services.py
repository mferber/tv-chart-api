from typing import Any

from litestar_users.service import BaseUserService

from .models import User


class UserService(BaseUserService[User, Any, Any]):  # type: ignore[type-var]
    pass
