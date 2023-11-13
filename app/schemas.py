from pydantic import BaseModel, EmailStr
from typing import Optional
from pydantic.types import conint

"""Create User"""
class UserCreate(BaseModel):
    """
    Pydantic model for creating a new user.

    Attributes:
        username (str): The username of the new user.
        email (EmailStr): The email address of the new user.
        password (str): The password of the new user.
        role (str): The role of the new user.
    """
    username: str
    email: EmailStr
    password: str
    role: str

class UserOut(BaseModel):
    """
    Pydantic model for user output.

    Attributes:
        user_id (int): The user's ID.
        username (str): The username of the user.
        email (EmailStr): The email address of the user.
    """
    user_id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

"""Login User"""
class UserLoginIn(BaseModel):
    """
    Pydantic model for user login.

    Attributes:
        email (EmailStr): The email address of the user for login.
        password (str): The password of the user for login.
    """
    email: EmailStr
    password: str

class Token(BaseModel):
    """
    Pydantic model for API token.

    Attributes:
        access_token (str): The access token.
        token_type (str): The type of the token.
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Pydantic model for token data.

    Attributes:
        id (Optional[str]): Optional user ID.
    """
    id: Optional[str] = None

class ChangePassword(BaseModel):
    """
    Pydantic model for changing user password.

    Attributes:
        password (str): The new password.
    """
    password: str

class UserEmail(BaseModel):
    """
    Pydantic model for user email.

    Attributes:
        user_email (EmailStr): The user's email address.
    """
    user_email: EmailStr

class VerifyPin(BaseModel):
    """
    Pydantic model for pin verification.

    Attributes:
        pin_number (str): The pin number to be verified.
        email (EmailStr): The email address associated with the pin.
    """
    pin_number: str
    email: EmailStr

class ResetPassword(BaseModel):
    """
    Pydantic model for resetting user password.

    Attributes:
        email (EmailStr): The email address of the user.
        password (str): The new password.
    """
    email: EmailStr
    password: str

class UserInput(BaseModel):
    """
    Pydantic model for user input.

    Attributes:
        message (str): The user input message.
        data (dict): Additional data.
        industry (str): The industry associated with the input.
    """
    message: str
    data: dict
    industry: str

class Text2SQL(BaseModel):
    """
    Pydantic model for text to SQL conversion.

    Attributes:
        message (str): The input message.
        industry (str): The industry associated with the input.
        language (str): The language of the input.
    """
    message: str
    industry: str
    language: str

class DatabaseConnection(BaseModel):
    """
    Pydantic model for database connection information.

    Attributes:
        database_host (str): The host address of the database.
        database_user (str): The username for database connection.
        database_name (str): The name of the database.
        database_password (str): The password for database connection.
    """
    database_host: str
    database_user: str
    database_name: str
    database_password: str
