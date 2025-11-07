import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):
    SMS_MOBILE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE: float = 0.7

    app_name: str = "SMS Mobile Gateway API"
    app_version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()