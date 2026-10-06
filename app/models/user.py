from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import EmailStr

USER_ROLES = frozenset({"student", "company", "department"})


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role: str = "student"
    full_name: str = ""


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)