# -*- coding: utf-8 -*-
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.jobs import jobs_bp
from app.routes.databases import databases_bp
from app.routes.emails import emails_bp
from app.routes.logs import logs_bp
from app.routes.tools import tools_bp

__all__ = ["main_bp", "auth_bp", "jobs_bp", "databases_bp", "emails_bp", "logs_bp", "tools_bp"]
