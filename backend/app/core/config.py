import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:2005@localhost:5432/secondhand"


def load_environment_file(path=BASE_DIR / ".env"):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


load_environment_file()


class BaseConfig:
    APP_NAME = os.getenv("APP_NAME", "SecondMarket")
    APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTH_SESSION_COOKIE_NAME = os.getenv("AUTH_SESSION_COOKIE_NAME", "secondmarket_session")
    AUTH_SESSION_DAYS = int(os.getenv("AUTH_SESSION_DAYS", "7"))
    FRONTEND_ROOT = str(BASE_DIR / "frontend")
    JSON_SORT_KEYS = False
    TESTING = False
    DEBUG = False
    ENV_NAME = "production"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV_NAME = "development"


class TestingConfig(BaseConfig):
    TESTING = True
    ENV_NAME = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    ENV_NAME = "production"


def get_config():
    env_name = os.getenv("FLASK_ENV", "development").lower()

    if env_name == "testing":
        return TestingConfig
    if env_name == "production":
        return ProductionConfig
    return DevelopmentConfig
