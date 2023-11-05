from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, utils, oauth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router = APIRouter(tags = ['Authentication'])

@router.post('/login', response_model = schemas.Token)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(),  db:Session = Depends(get_db)):
    #key in use form-data, username: ... , password: ...
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Invalid Credentials, no user")
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Invalid Credentials, wrong password")
    access_token = oauth2.create_access_token(data = {"user_id": user.user_id})
    refresh_token = oauth2.create_refresh_token(data = {"user_id": user.user_id})
    return {"access_token": access_token, "refresh_token":refresh_token,"token_type": "bearer"}

@router.post("/refresh", response_model=schemas.NewToken)
async def refresh_token(token: schemas.RefreshToken,db: Session = Depends(get_db)):
    refresh_token = token.refresh_token
    current_user = oauth2.get_current_user_with_refresh_token(refresh_token = refresh_token, db = db)
    new_access_token = oauth2.create_access_token(data={"user_id": current_user.user_id})
    return {"access_token": new_access_token, "token_type": "bearer"}

