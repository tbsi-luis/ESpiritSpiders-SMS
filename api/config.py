import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

load_dotenv()

class Settings(BaseSettings):
    SMS_MOBILE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.7

    DATABASE_HOST: str = "192.168.2.131"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "Espider_10282025"
    DATABASE_USER: str = "people_navee"
    DATABASE_PASSWORD: str = "admin@Adm!n"

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL"""
        # URL-encode password to handle special characters
        encoded_password = quote_plus(self.DATABASE_PASSWORD)

        return f"postgresql://{self.DATABASE_USER}:{encoded_password}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # Database Pool Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600


    app_name: str = "SMS Mobile Gateway API"
    app_version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()