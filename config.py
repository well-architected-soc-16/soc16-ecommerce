import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")        
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not SECRET_KEY or not DATABASE_URL:            
        raise RuntimeError("SECRET_KEY dan DATABASE_URL wajib diisi di .env")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"