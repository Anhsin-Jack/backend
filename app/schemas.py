from pydantic import BaseModel, EmailStr
from typing import Optional

from pydantic.types import conint

class UserCreate(BaseModel):
    username : str
    email: EmailStr
    password: str
    confirm_password: str
    role: str

class UserOut(BaseModel):
    user_id: int
    username : str
    email: EmailStr

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class NewToken(BaseModel):
    access_token:str
    token_type:str

class RefreshToken(BaseModel):
    refresh_token:str


class TokenData(BaseModel):
    id: Optional[str] = None


class Vote(BaseModel):
    post_id: int
    dir: conint(le=1)

class Questions(BaseModel):
    question: str
    question_id : int

class ChangePassword(BaseModel):
    password: str

class Chatbot(BaseModel):
    query : str

class UserId(BaseModel):
    id : int
    update_username: str
class UserlistKeyword(BaseModel):
    keyword : str