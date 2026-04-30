from pydantic import BaseModel


class UserPrefs(BaseModel):
    show_favorites_only: bool = False
