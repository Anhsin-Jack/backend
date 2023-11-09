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
    openai_api_key: str
    openai_organization: str
    database_user:str
    database_password:str
    database_host: str
    database_name: str
    aws_access_key: str
    aws_secret_key:str
    aws_bucket_name:str
    
    class Config:
        env_file = ".env"

settings = Settings()