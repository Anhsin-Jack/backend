from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_name: str
    secret_key : str
    algorithm : str
    access_token_expire_minutes : int
    refresh_token_expire_hours: int
    
    class Config:
        env_file = ".env"

settings = Settings()