from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.orm import Session
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
from database import get_db
import schemas, models, utils, oauth2
import random, string, smtplib, redis
from fastapi.responses import JSONResponse
from config import settings
from redis import Redis
from database import get_redis_client

access_token_expiration_time = settings.access_token_expire_hours*60*60 
refresh_token_expiration_time = settings.refresh_token_expire_weeks*7*24*60*60

pin_expiration_time = settings.pin_expiration_time # 5 minutes

router = APIRouter(
    prefix="/auth",
    tags=['Authentication']
)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.

    **Input:**
    - `user` (schemas.UserCreate): User creation request object containing the following fields:
        - `username` (str): User's username.
        - `email` (EmailStr): User's email address.
        - `password` (str): User's password.
        - `role` (str): User's role.

    **Output:**
    - `new_user` (schemas.UserOut): User creation response object containing:
        - `user_id` (int): Unique identifier for the newly created user.
        - `username` (str): User's username.
        - `email` (EmailStr): User's email address.

    **Raises:**
    - `HTTPException` with status code 404 if password and confirm password do not match.
    - `HTTPException` with status code 400 if there is an issue during user creation.

    **Procedure:**
    1. Hash the user's password for security.
    2. Create a dictionary representation of the user object.
    3. Remove the `confirm_password` field from the dictionary.
    4. Create a new user instance with the modified dictionary.
    5. Add the new user to the database, commit the transaction, and refresh the user instance.
    6. Rollback the transaction and raise an exception if there are any issues during the process.
    """
    check_user = db.query(models.User).filter(models.User.email == user.email).first()
    if check_user:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = f"This email already registered: {user.email}")
    # hash the password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    user_dict = user.model_dump()
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

@router.post('/login', response_model = schemas.Token)
async def login(user_info: schemas.UserLoginIn,  db:Session = Depends(get_db)):
    """
    Log in to the dashboard and generate access and refresh tokens.

    **Input:**
    - `user_info` (schemas.UserLoginIn): User login request object containing:
        - `email` (EmailStr): User's email address.
        - `password` (str): User's password.

    **Output:**
    - A dictionary containing:
        - `access_token` (str): Token to be used in the Authorization header.
        - `token_type` (str): Always "bearer".

    **Raises:**
    - `HTTPException` with status code 401 if the provided credentials are invalid.

    :param user_info: User login request payload.
    :type user_info: schemas.UserLoginIn
    :param db: Database session dependency.
    :type db: Session
    :return: Dictionary with access token and token type.
    :rtype: dict
    """
    r = redis.Redis(host='localhost', port=6379, db=0)
    user = db.query(models.User).filter(models.User.email == user_info.email).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid Credentials, no user")
    if not utils.verify(user_info.password, user.password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid Credentials, wrong password")
    access_token, refresh_token = oauth2.create_access_refresh_token(data = {"user_id": user.user_id})
    r.setex(f"{user.user_id}:access_token", access_token_expiration_time, access_token)
    r.setex(f"{user.user_id}:refresh_token", refresh_token_expiration_time, refresh_token)
    return {"access_token": access_token,"token_type": "bearer","expires_in":access_token_expiration_time}

@router.post('/logout')
async def logout(db: Session = Depends(get_db),access_token :str =  Header(None),r:Redis = Depends(get_redis_client)):
    current_user = utils.authentication(access_token,db)
    try:
        r.delete(f"{current_user.user_id}:access_token")
        r.delete(f"{current_user.user_id}:refresh_token")
    except ConnectionError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to connect to the Redis server")
    return JSONResponse(content={"message": "Successfully logout"}, status_code=200)
    
@router.post("/refresh_token/{user_id}", response_model = schemas.Token)
async def refresh_token(user_id:int):
    """
        This function is to refresh the access token.
        Input:
            token: (refresh_token)
        Output:
            A dictionary contains:
            access_token: to be used in the Authorization header
            token_type: always bearer
    """
    r = redis.Redis(host='localhost', port=6379, db=0)
    refresh_token = r.get(f"{user_id}:refresh_token")
    if not refresh_token:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Refresh token expired or does not exist with user_id: {user_id}")
    new_access_token, _ = oauth2.create_access_refresh_token(data={"user_id": user_id}, is_access_only=True)
    r.setex(f"{user_id}:access_token", access_token_expiration_time, new_access_token)
    refresh_token = refresh_token.decode('utf-8')
    r.expire(f"{user_id}:refresh_token", refresh_token_expiration_time)
    return {"access_token": new_access_token, "token_type": "bearer","expires_in":access_token_expiration_time}


@router.post('/send_pin')
async def send_pin(user_email:schemas.UserEmail, db: Session = Depends(get_db)):
    """
        This function is to send pin to user email when user forgot password, user need to receive pin for verification.
        Input:
            user_email: (user_email)
        Output:
            A dictionary contains:
            pin_status: True if the email is sent successfully
    """
    r = redis.Redis(host='localhost', port=6379, db=0)
    user_email = user_email.user_email
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Invalid Credentials, no user")
    
    # Generate a random PIN with the specified length (default is 6 digits)
    characters = string.digits
    pin = ''.join(random.choice(characters) for _ in range(6))
    r.setex(f"{user_email}:pin", pin_expiration_time, pin)

    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "c.f.y11303@gmail.com"
    sender_password = "eaqlayonlqvkvpjf"

    # Create the email message
    subject = "Your PIN"
    body = f"Your PIN is: {pin}"
    message = f"Subject: {subject}\n\n{body}"

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        # Log in to your sender email account
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, user_email, message)

        # Close the connection
        server.quit()

        return JSONResponse(content={"message": f"Successfully send pin to email: {user_email}"}, status_code=200)
    except smtplib.SMTPException as e:
        str_e = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Failed to send email: {str_e}")

@router.post('/verify_pin')
async def verify_pin(verify_pin:schemas.VerifyPin):
    """
        This function is to send pin to user email when user forgot password, user need to receive pin for verification.
        Input:
            user_email: (user_email)
        Output:
            A dictionary contains:
            pin_status: True if the email is sent successfully
    """
    r = redis.Redis(host='localhost', port=6379, db=0)
    pin = verify_pin.pin_number
    email = verify_pin.email
    stored_pin = r.get(f"{email}:pin")
    if not stored_pin: #
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"PIN has expired or does not exist: {pin}")
    stored_pin = stored_pin.decode('utf-8')
    if stored_pin != pin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Wrong pin number: {pin}")
    return JSONResponse(content={"message": "Verify pin sucessfully."}, status_code=200)

@router.post('/reset_password')
async def reset_password(user_info: schemas.ResetPassword, db: Session = Depends(get_db)):
    """
        This function is to reset user's password.
        Input:
            password: schemas.ResetPassword
            (email: EmailStr
            password: str)
        Output:
            A dictionary contains:
            reset_password_status : True if reset password sucessful.
    """
    user_query = db.query(models.User).filter(models.User.email == user_info.email)
    user = user_query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"password with email: {user_info.email} does not exist")
    hashed_password = utils.hash(user_info.password)
    if user.password != hashed_password:
        user_query.update({"password":hashed_password},synchronize_session=False)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    return JSONResponse(content={"message": f"Reset password sucessfully."}, status_code=200)



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

