import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "MNOS.CUSTOMSBRIDGE"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/v1/customsbridge"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://jules:password@localhost:5432/customsbridge")

    # MNOS Core Services
    AQUA_URL: str = os.getenv("AQUA_URL", "http://mnos-aqua:8000")
    ODYSSEY_URL: str = os.getenv("ODYSSEY_URL", "http://mnos-odyssey:8000")
    SKYGODOWN_URL: str = os.getenv("SKYGODOWN_URL", "http://mnos-skygodown:8000")
    FCE_URL: str = os.getenv("FCE_URL", "http://mnos-fce:8005")
    AEGIS_URL: str = os.getenv("AEGIS_URL", "http://mnos-aegis:8001")
    SHADOW_URL: str = os.getenv("SHADOW_URL", "http://mnos-shadow:8002")
    EVENTS_URL: str = os.getenv("EVENTS_URL", "http://mnos-events:8004")
    ELEONE_URL: str = os.getenv("ELEONE_URL", "http://mnos-eleone:8003")

    # Security
    CUSTOMS_TOKEN: str = os.getenv("CUSTOMS_TOKEN", "secret-customs-token")

    class Config:
        env_file = ".env"

settings = Settings()
