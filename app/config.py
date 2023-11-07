from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_name: str
    secret_key : str
    algorithm : str
    access_token_expire_weeks : int
    refresh_token_expire_weeks: int
    pin_expiration_time : int
    
    class Config:
        env_file = ".env"

settings = Settings()