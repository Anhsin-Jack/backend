from jose import JWTError, jwt
from datetime import datetime, timedelta
from . import database, models
from fastapi import status, HTTPException, Depends
from sqlalchemy.orm import Session
from .config import settings
import redis


SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_WEEK = settings.access_token_expire_weeks 
REFRESH_TOKEN_EXPIRE_WEEK = settings.refresh_token_expire_weeks

def create_access_refresh_token(data : dict, is_access_only = False):
    to_encode_access = data.copy()
    expire_access = datetime.utcnow() + timedelta(weeks=ACCESS_TOKEN_EXPIRE_WEEK)
    to_encode_access.update({"exp":expire_access})
    encoded_jwt_access = jwt.encode(to_encode_access, SECRET_KEY, algorithm=ALGORITHM)

    if not is_access_only:
        to_encode_refresh = data.copy()
        expire_refresh = datetime.utcnow() + timedelta(weeks=REFRESH_TOKEN_EXPIRE_WEEK)
        to_encode_refresh.update({"exp":expire_refresh})
        encoded_jwt_refresh = jwt.encode(to_encode_refresh, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt_access, encoded_jwt_refresh
    return encoded_jwt_access, ""

def verify_access_token(token : str, credentials_exception):
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        access_token = r.get(f"{id}:access_token")
        if not access_token:
            raise credentials_exception
        access_token = access_token.decode('utf-8')
        if token != access_token:
            raise credentials_exception
    except JWTError as e:
        print(e)
        raise credentials_exception
    return id

def get_current_user(token: str, db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    user_id = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    return user