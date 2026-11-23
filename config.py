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

    AUDIT_LOG_PATH = os.environ.get("AUDIT_LOG_PATH", "logs/audit.log")
    TRUST_PROXY = os.environ.get("TRUST_PROXY", "0") == "1"

    # Catatan Num WhatsApp toko (harus 62xxx). if Kosong = tombol WA tidak ditampilkan.
    WA_TOKO = os.environ.get("WA_TOKO", "")
