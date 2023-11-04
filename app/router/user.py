from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import schemas, models, utils, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.post("/create_user", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    #Check password and confirm password
    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Password and confirm password do not match")

    # hash the password - user.password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    user_dict = user.model_dump()
    user_dict.pop("confirm_password")
    print(user_dict)
    new_user = models.User(**user_dict)
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    return new_user

@router.get('/get_user/{user_id}', response_model=schemas.UserOut)
async def get_user(user_id: int, db: Session = Depends(get_db),current_user = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} does not exist")
    return user

@router.post('/change_password')
async def change_password(password: schemas.ChangePassword, db: Session = Depends(get_db), current_user = Depends(oauth2.get_current_user)):
    user_query = db.query(models.User).filter(models.User.user_id == current_user.user_id)
    user = user_query.first()
    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"password with id: {current_user.id} does not exist")
    hashed_password = utils.hash(password.password)
    if user.password != hashed_password:
        user_query.update({"password":hashed_password},synchronize_session=False)
        db.commit()
    return {"change_status":True}