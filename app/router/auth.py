from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import sys
sys.path.append("/Users/michaelchee/Documents/backend/app")
from database import get_db
import schemas, models, utils, oauth2
import random, string, smtplib, redis
from fastapi.responses import JSONResponse
from config import settings

access_token_expiration_time = settings.access_token_expire_weeks*7*24*60*60 # 1 month
refresh_token_expiration_time = settings.refresh_token_expire_weeks*7*24*60*60 # 1 year

pin_expiration_time = settings.pin_expiration_time # 5 minutes

router = APIRouter(
    prefix="/auth",
    tags=['Authentication']
)

@router.post('/login', response_model = schemas.Token)
async def login(user_info: schemas.UserLoginIn,  db:Session = Depends(get_db)):
    """
        This api is used to login to the dashboard.
        Input:
            user_credentials: (username, password)
        Output:
            A dictionary contains:
            access_token: to be used in the Authorization header
            token_type: always bearer
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
    return {"access_token": access_token,"token_type": "bearer"}

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
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post('/send_pin_to_email')
async def send_pin_to_email(user_email:schemas.UserEmail, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Invalid Credentials, no user")
    
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
            password: str
            confirm_password:str)
        Output:
            A dictionary contains:
            reset_password_status : True if reset password sucessful.
    """
    user_query = db.query(models.User).filter(models.User.email == user_info.email)
    user = user_query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"password with email: {user_info.email} does not exist")
    if user_info.password != user_info.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Confirm Password and Password not the same")
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
