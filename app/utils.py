from passlib.context import CryptContext
from fastapi import HTTPException, status, Request
from starlette.types import Message
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
import sys, os, time, random, string

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from . import oauth2
from .models import User
from .config import settings
from .logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")
SECRET_KEY = settings.secret_key_encryp
cipher_suite = Fernet(SECRET_KEY)

def hash(password: str)-> bool:
    """
    Hashes the given password using bcrypt.

    Args:
        password (str): The password to be hashed.

    Returns:
        bool: The hashed password.
    """
    return pwd_context.hash(password)

def verify(plain_password, hashed_password)->bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password: The plain password.
        hashed_password: The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def authentication(access_token:str, db: Session) -> User:
    """
    Performs user authentication based on the provided access token.

    Args:
        access_token (str): The access token for authentication.
        db (Session): The database session.

    Returns:
        models.User: The authenticated user.

    Raises:
        HTTPException: If authentication fails.
    """
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"No authentication token provided")
    current_user = oauth2.get_current_user(access_token, db)
    
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"No current user found")
    return current_user

def encrypt_data(data:str) -> str:
    """
    Encrypts the given data using Fernet encryption.

    Args:
        data (str): The data to be encrypted.

    Returns:
        str: The encrypted data.
    """
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypts the given encrypted data using Fernet decryption.

    Args:
        encrypted_data (str): The encrypted data.

    Returns:
        str: The decrypted data.
    """
    return cipher_suite.decrypt(encrypted_data.encode()).decode()


def generate_unique_id():
    """
    Generates a unique ID based on timestamp and random characters.

    Returns:
        str: The generated unique ID.

    Raises:
        Exception: If an error occurs during the ID generation process.
    """
    try:
        timestamp = int(time.time())
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        unique_id = f'{timestamp}_{random_string}'
        return unique_id
    
    except Exception as e:
        logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
        raise e 
    

async def set_body(
        request: Request, 
        body: bytes
    ):
    """
    Set the request body for the given request.

    Args:
        request (Request): The request object.
        body (bytes): The request body in bytes.
    """
    async def receive() -> Message:
        return {"type": "http.request", "body": body}
    request._receive = receive