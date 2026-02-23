import datetime

from litestar.security.jwt import JWTCookieAuth
from litestar_users import LitestarUsersConfig, LitestarUsersPlugin
from litestar_users.config import (
    AuthHandlerConfig,
    CurrentUserHandlerConfig,
    PasswordResetHandlerConfig,
    RegisterHandlerConfig,
    UserManagementHandlerConfig,
)

from .dtos import UserReadDTO, UserRegistrationDTO, UserUpdateDTO
from .models import User
from .services import UserService


def configure_litestar_users_plugin(jwt_encoding_secret: str) -> LitestarUsersPlugin:
    """Creates main litestar-users plugin object with many, many configuration options.

    Args:
      jwt_encoding_secret: signing secret for JWTs
    """

    return LitestarUsersPlugin(
        config=LitestarUsersConfig(
            # which type of authentication to use
            auth_backend_class=JWTCookieAuth,
            # True to require email verification after user registers
            require_verification_on_registration=False,  # for now assume emails are fine
            # JWT signing secret
            secret=jwt_encoding_secret,
            # Cookie expiration
            default_token_expiration=datetime.timedelta(days=30),
            # SQLAlchemy model for user records
            user_model=User,
            # DTO for registering users to db
            user_registration_dto=UserRegistrationDTO,
            # DTO for reading users from db (excludes password hash)
            user_read_dto=UserReadDTO,
            # DTO for updating user information in db (excludes password hash)
            user_update_dto=UserUpdateDTO,
            # Service class that handles all user/authentication-related operations
            user_service_class=UserService,
            # Setup for login and logout handlers
            auth_handler_config=AuthHandlerConfig(
                login_path="/auth/login", logout_path="/auth/logout"
            ),
            # Setup for current-user handler
            current_user_handler_config=CurrentUserHandlerConfig(path="/auth/users/me"),
            # Setup for forgot/reset password handler
            password_reset_handler_config=PasswordResetHandlerConfig(
                forgot_path="/auth/forgot-password", reset_path="/auth/reset-password"
            ),
            # Setup for user registration handler
            register_handler_config=RegisterHandlerConfig(path="/auth/register"),
            # Setup for user management handler
            user_management_handler_config=UserManagementHandlerConfig("/auth/users"),
        )
    )
