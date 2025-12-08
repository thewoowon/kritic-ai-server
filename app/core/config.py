from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List, Union


class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Kritic API"
    BACKEND_CORS_ORIGINS: List[str] = []
    DEBUG: bool = True

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            # Handle comma-separated string
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return []

    class Config:
        case_sensitive = True


settings = Settings()
