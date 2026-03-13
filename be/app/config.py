import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60")
    )
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'water_quality.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000/predict")
    AI_SERVICE_TIMEOUT = int(os.getenv("AI_SERVICE_TIMEOUT", "5"))
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL = os.getenv("EMAIL", "letrananhdung234@gmail.com")
    PASSWORD = os.getenv("PASSWORD", "dfja dypj uhro hygm")
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "anhdungletran123@gmail.com")
