from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyInitPlugin
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.security.session_auth import SessionAuth
from litestar_users import LitestarUsersConfig, LitestarUsersPlugin
from litestar_users.config import (
    AuthHandlerConfig,
    CurrentUserHandlerConfig,
    PasswordResetHandlerConfig,
    RegisterHandlerConfig,
    UserManagementHandlerConfig,
    VerificationHandlerConfig,
)

from .dtos import UserReadDTO, UserRegistrationDTO, UserUpdateDTO
from .models import User
from .services import UserService
from .startup import get_litestar_sqlalchemy_async_config

# if TYPE_CHECKING:
#     from litestar.connection import ASGIConnection
#     from litestar.handlers.base import BaseRouteHandler

ENCODING_SECRET = "1234567890abcdef"  # TODO: env var with secrets management


def configure_litestar_users_plugin():
    return LitestarUsersPlugin(
        config=LitestarUsersConfig(
            auth_backend_class=SessionAuth,
            session_backend_config=ServerSideSessionConfig(),
            secret=ENCODING_SECRET,
            user_model=User,
            user_read_dto=UserReadDTO,
            user_registration_dto=UserRegistrationDTO,
            user_update_dto=UserUpdateDTO,
            user_service_class=UserService,
            auth_handler_config=AuthHandlerConfig(
                login_path="/auth/login", logout_path="/auth/logout"
            ),
            current_user_handler_config=CurrentUserHandlerConfig(path="/auth/users/me"),
            password_reset_handler_config=PasswordResetHandlerConfig(
                forgot_path="/auth/forgot-password", reset_path="/auth/reset-password"
            ),
            register_handler_config=RegisterHandlerConfig(path="/auth/register"),
            user_management_handler_config=UserManagementHandlerConfig("/auth/users"),
            verification_handler_config=VerificationHandlerConfig("/auth/verify"),
        )
    )


def get_litestar_users_sqlalchemy_init_plugin(db_url):
    return SQLAlchemyInitPlugin(config=get_litestar_sqlalchemy_async_config(db_url))
