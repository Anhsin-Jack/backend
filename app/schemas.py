from pydantic import BaseModel, EmailStr
from typing import Optional
from pydantic.types import conint

"""Create User"""
class UserCreate(BaseModel):
    username : str
    email: EmailStr
    password: str
    role: str

class UserOut(BaseModel):
    user_id: int
    username : str
    email: EmailStr

    class Config:
        from_attributes = True

"""Login User"""
class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None


class ChangePassword(BaseModel):
    password: str

class UserEmail(BaseModel):
    user_email:EmailStr

class VerifyPin(BaseModel):
    pin_number:str
    email:EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    password: str

class UserInput(BaseModel):
    message: str
    data:dict
    industry:str

class Text2SQL(BaseModel):
    message: str
    industry:str
    language:str

class DatabaseConnection(BaseModel):
    database_host:str
    database_user:str
    database_name:str
    database_password:str

class CSVData(BaseModel):
    csv_id:str