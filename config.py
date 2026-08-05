import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """Base Configuration Class"""

    SECRET_KEY = os.getenv("SECRET_KEY", "ai-shopping-assistant-super-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost").strip()
    DB_PORT = os.getenv("DB_PORT", "3306").strip()
    DB_USER = os.getenv("DB_USER", "root").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "ai_shopping_assistant").strip()

    # Encode password safely (supports @, #, %, &, ?, :, /, etc.)
    ENCODED_PASSWORD = quote_plus(DB_PASSWORD)

    # Build Database URI
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{ENCODED_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Gemini API Key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class DevelopmentConfig(Config):
    """Development Configuration"""
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    """Production Configuration"""
    DEBUG = False
    ENV = "production"


class TestingConfig(Config):
    """Testing Configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}