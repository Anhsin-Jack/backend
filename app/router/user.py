from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Header
from sqlalchemy.orm import Session
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
import schemas, models, utils
from database import get_db
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.post("/create_user", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
        This api is to create a new user.
        Input:
            user: schemas.UserCreate
            (username : str
            email: EmailStr
            password: str
            confirm_password: str
            role: str)
        Output:
            new_user: User
            (user_id: int
            username : str
            email: EmailStr)
    """
    #Check password and confirm password
    if user.password != user.confirm_password:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Password and confirm password do not match")
    # hash the password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    user_dict = user.model_dump()
    user_dict.pop("confirm_password")
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
async def get_user(user_id: int, db: Session = Depends(get_db), access_token :str =  Header(None)):
    """
        This api is to get user details depends on the user id.
        Input:
            user_id : int

        Output:
            user: User
            (user_id: int
            username : str
            email: EmailStr)
    """
    print(access_token)
    utils.authentication(access_token,db)
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {user_id} does not exist")
    return user

@router.post('/change_password')
async def change_password(password: schemas.ChangePassword, db: Session = Depends(get_db), access_token :str =  Header(None)):
    """
        This api is to change user's password.
        Input:
            password: schemas.ChangePassword
            (password: str)
        Output:
            A JSONResponse contains message "Successfully change password" if change password sucessful.
    """
    current_user = utils.authentication(access_token,db)
    user_query = db.query(models.User).filter(models.User.user_id == current_user.user_id)
    user = user_query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"password with id: {current_user.user_id} does not exist")
    hashed_password = utils.hash(password.password)
    if user.password != hashed_password:
        user_query.update({"password":hashed_password},synchronize_session=False)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    return JSONResponse(content={"message": "Successfully change password"}, status_code=200)