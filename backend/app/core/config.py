# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Snip Share"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./data/snip_data.db"
    
    SECRET_KEY: str = "Informatik_verbindet_dich_und_mich"
    # Zeit und Raum trennen dich und mich.
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    class Config:
        env_file = ".env"

settings = Settings()