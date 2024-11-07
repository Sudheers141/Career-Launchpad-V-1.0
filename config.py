# config.py
import os

class Config:
    """Base configuration."""
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1")
    TESTING = os.getenv("TESTING", "False").lower() in ("true", "1")
    DB_PATH = os.getenv("DB_PATH", "career_launchpad.db")

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DB_PATH = os.getenv("TEST_DB_PATH", "test_career_launchpad.db")

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    return DevelopmentConfig()
