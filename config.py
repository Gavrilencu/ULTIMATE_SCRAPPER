# -*- coding: utf-8 -*-
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-scrapper-ultimate")
# Cale universală Windows/Linux: folosim forward slashes în URI pentru SQLite
_db_path = (BASE_DIR / "app.db").as_posix()
SQLALCHEMY_DATABASE_URI = f"sqlite:///{_db_path}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SCHEDULER_API_ENABLED = False
# Fus orar pentru programare joburi și afișare în aplicație (ora Chișinău, Moldova)
TIMEZONE = os.environ.get("TIMEZONE", "Europe/Chisinau")
