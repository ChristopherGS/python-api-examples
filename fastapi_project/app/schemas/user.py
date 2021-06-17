from pydantic import BaseModel

from typing import Optional


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False


class CreateUser(User):
    password: str


class UserInDB(User):
    hashed_password: str
