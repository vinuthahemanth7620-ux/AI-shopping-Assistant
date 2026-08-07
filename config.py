import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"), override=True)


class Config:
    """Base Configuration Class"""

    # Secret Key for Flask sessions and CSRF protection
    SECRET_KEY = os.getenv("SECRET_KEY", "ai-shopping-assistant-super-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Configuration Parameters
    DB_HOST = os.getenv("DB_HOST", "localhost").strip()
    DB_PORT = os.getenv("DB_PORT", "3306").strip()
    DB_USER = os.getenv("DB_USER", "root").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip()
    DB_NAME = os.getenv("DB_NAME", "ai_shopping_assistant").strip()

    # Safely URL-encode special characters in password (@, #, %, &, ?, :, /, etc.)
    ENCODED_PASSWORD = quote_plus(DB_PASSWORD)

    # Build Database URI
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Gemini API Key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    # Application Base URL for Mobile & Cross-Device Email Approval Links
    APP_HOST_URL = os.getenv("APP_HOST_URL", "").strip()

    # Gmail SMTP Email Configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com").strip()
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ["true", "1", "yes"]
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() in ["true", "1", "yes"]
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "").strip()
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "").strip()
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "").strip() or MAIL_USERNAME or "noreply@aishoppingassistant.com"

    # Security & OTP Configurations
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", 5))

    # Session & Cookie Security Configuration for Email Link Authentication
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True



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