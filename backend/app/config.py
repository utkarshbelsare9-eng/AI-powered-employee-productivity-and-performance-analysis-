import os
from datetime import timedelta
from dotenv import load_dotenv

# BASE_DIR points to backend directory
BACKEND_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(BACKEND_DIR))

# Load .env from project root or backend root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))


class Config:
    # ---- Core ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-super-secret-key-in-production")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", 24))

    # ---- Email / Password Reset ----
    FORGOT_PASSWORD_TARGET_EMAIL = os.environ.get("FORGOT_PASSWORD_TARGET_EMAIL", "utkarshbelsare9@gmail.com")
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("true", "1", "t", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")

    # ---- Database ----
    MYSQL_USER = os.environ.get("MYSQL_USER")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
    MYSQL_DB = os.environ.get("MYSQL_DB", "employee_productivity_ai")

    if MYSQL_USER and MYSQL_PASSWORD:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:"
            f"{MYSQL_PORT}/{MYSQL_DB}"
        )
    else:
        DB_PATH = os.path.join(PROJECT_ROOT, "database", "app.db")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Storage Paths ----
    PROJECT_ROOT = PROJECT_ROOT
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "storage", "uploads")
    REPORTS_FOLDER = os.path.join(PROJECT_ROOT, "storage", "reports")
    MODEL_FOLDER = os.path.join(PROJECT_ROOT, "ml_artifacts")
    DATASET_FOLDER = os.path.join(PROJECT_ROOT, "datasets")
    
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "png", "jpg", "jpeg"}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    # ---- Session ----
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    # ---- Security ----
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ---- CORS Configuration for Mobile & Web ----
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
