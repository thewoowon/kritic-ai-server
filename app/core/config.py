from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Kritic API"
    DEBUG: bool = True

    # Use Optional[str] and parse manually to avoid Pydantic JSON parsing issues
    BACKEND_CORS_ORIGINS_STR: Optional[str] = None

    class Config:
        case_sensitive = True
        # Don't try to parse BACKEND_CORS_ORIGINS as JSON
        env_prefix = ""

    @property
    def BACKEND_CORS_ORIGINS(self):
        """Parse CORS origins from string"""
        if not self.BACKEND_CORS_ORIGINS_STR:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS_STR.split(",") if origin.strip()]


# Get BACKEND_CORS_ORIGINS from environment manually
_cors_origins = os.getenv("BACKEND_CORS_ORIGINS", "")
settings = Settings(BACKEND_CORS_ORIGINS_STR=_cors_origins if _cors_origins else None)
