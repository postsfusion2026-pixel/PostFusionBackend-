from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "PostsFusionBackend"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = ""

    # Auth
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    class Config:
        env_file = ".env"

settings = Settings()