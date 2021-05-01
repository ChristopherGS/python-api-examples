import json
import logging
import pathlib
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID
import sys

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    BaseSettings,
    EmailStr,
    Field,
    HttpUrl,
    PostgresDsn,
    validator,
)
from loguru import logger

# Project Directories
ROOT = pathlib.Path(__file__).resolve().parent.parent


def _list_parse_fallback(v: Any) -> Any:
    try:
        return json.loads(v)
    except Exception:
        return v.split(",")


class LoggingSettings(BaseSettings):
    LOGGING_LEVEL: int = logging.INFO  # logging levels are ints


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    JWT_SECRET: str = "TEST_SECRET_DO_NOT_USE_IN_PROD"

    # 60 minutes * 24 hours * 30 days = 30 days
    CONFIRMATION_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    EMAIL_CONFIRMATION_REDIRECT_URL: str = (
        f"http://localhost:8001{API_V1_STR}/users/confirm"
    )
    PASSWORD_RESET_REDIRECT_URL: str = (
        f"http://localhost:8001{API_V1_STR}/users/new-password"
    )

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ALLOWED_SCOPES: Mapping[str, set] = {
        "global_user": {
            "me",
        },
    }

    # Meta
    logging: LoggingSettings = LoggingSettings()

    DOMAIN: str = "localhost:8001"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8001"  # type: ignore

    # BACKEND_CORS_ORIGINS is a comma-separated list of origins
    # e.g: http://localhost,http://localhost:4200,http://localhost:3000
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # type: ignore
        "http://localhost:8000",  # type: ignore
        "https://localhost:3000",  # type: ignore
        "https://localhost:8000",  # type: ignore
        "http://api.coursemaker.io",  # type: ignore
        "https://api.coursemaker.io",  # type: ignore
    ]
    # Origins that match this regex OR are in the above list are allowed
    BACKEND_CORS_ORIGIN_REGEX: Optional[
        str
    ] = "https.*\.(netlify.app)"  # noqa: W605

    PROJECT_NAME: str = "fastapi-example"

    class Config:
        case_sensitive = True
        json_loads = _list_parse_fallback


def setup_app_logging(config: Settings) -> None:
    """Prepare custom logging for our application."""
    LOGGERS = ("uvicorn.asgi", "uvicorn.access")
    for logger_name in LOGGERS:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler(level=config.logging.LOGGING_LEVEL)]

    logger.configure(
        handlers=[{"sink": sys.stderr, "level": config.logging.LOGGING_LEVEL}]
    )


settings = Settings()
