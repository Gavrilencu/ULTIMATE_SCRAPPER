# -*- coding: utf-8 -*-
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-scrapper-ultimate")
# Config bază de date aplicație: SQLite (implicit) / PostgreSQL / MySQL
_default_sqlite_path = (BASE_DIR / "app.db").as_posix()
APP_DB_BACKEND = (os.environ.get("APP_DB_BACKEND", "sqlite") or "sqlite").lower()
APP_DB_NAME = os.environ.get("APP_DB_NAME", "scrapper_ultimate")
APP_DB_HOST = os.environ.get("APP_DB_HOST", "localhost")
APP_DB_PORT = os.environ.get("APP_DB_PORT")  # string sau None
APP_DB_USER = os.environ.get("APP_DB_USER", "")
APP_DB_PASSWORD = os.environ.get("APP_DB_PASSWORD", "")

if APP_DB_BACKEND in ("postgres", "postgresql"):
    from urllib.parse import quote_plus
    user = quote_plus(APP_DB_USER)
    pwd = quote_plus(APP_DB_PASSWORD)
    port = APP_DB_PORT or "5432"
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{user}:{pwd}@{APP_DB_HOST}:{port}/{APP_DB_NAME}"
elif APP_DB_BACKEND == "mysql":
    from urllib.parse import quote_plus
    user = quote_plus(APP_DB_USER)
    pwd = quote_plus(APP_DB_PASSWORD)
    port = APP_DB_PORT or "3306"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{user}:{pwd}@{APP_DB_HOST}:{port}/{APP_DB_NAME}"
else:
    # SQLite local (implicit)
    _db_path = (BASE_DIR / os.environ.get("APP_DB_SQLITE_FILE", "app.db")).as_posix()
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{_db_path}"

SQLALCHEMY_TRACK_MODIFICATIONS = False
SCHEDULER_API_ENABLED = False
# Path de bază pentru toată aplicația (ex: /scrapper)
BASE_PATH = os.environ.get("BASE_PATH", "/scrapper")
# Fus orar pentru programare joburi și afișare în aplicație (ora Chișinău, Moldova)
TIMEZONE = os.environ.get("TIMEZONE", "Europe/Chisinau")
