from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
import oauth2
import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash(password: str)-> bool:
    return pwd_context.hash(password)

def verify(plain_password, hashed_password)->bool:
    return pwd_context.verify(plain_password, hashed_password)

def authentication(access_token:str, db: Session) -> models.User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"No authentication token provided")
    current_user = oauth2.get_current_user(access_token, db)
    
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"No current user found")
    return current_user