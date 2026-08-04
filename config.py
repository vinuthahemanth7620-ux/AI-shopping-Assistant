import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base Configuration Class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ai-shopping-assistant-super-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Configuration
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'ai_shopping_assistant')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # AI Gemini Integration Configuration (Placeholder for later phase)
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')


class DevelopmentConfig(Config):
    """Development Environment Configuration"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Production Environment Configuration"""
    DEBUG = False
    ENV = 'production'


class TestingConfig(Config):
    """Testing Environment Configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
