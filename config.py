"""
Hostel Complaint Management System (HCMS)
Configuration Module (config.py)
"""

import os
from datetime import timedelta
# Built-in zero-dependency .env loader
def _load_env_file(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v

_load_env_file()


class Config:
    # Flask Security & Session Management
    SECRET_KEY = os.environ.get("SECRET_KEY", "hcms_secure_secret_key_2026_default_replace")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Set to True in HTTPS production
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Database Connection Pool Settings
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "hostel_complaint_db")
    DB_POOL_NAME = "hcms_mysql_pool"
    DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", 10))
    
    # File Upload Restrictions
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB maximum file upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}
    
    # Application Metadata
    APP_NAME = "Hostel Complaint Management System"
    APP_VERSION = "1.0.0"
