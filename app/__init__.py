# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_class="config"):
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config_class)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Autentificați-vă pentru a accesa această pagină."

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.time_utils import format_local_datetime, get_app_timezone
    @app.template_filter("local_time")
    def local_time_filter(dt, fmt="%d.%m.%Y %H:%M:%S"):
        if dt is None:
            return "—"
        from flask import current_app
        tz = get_app_timezone(current_app)
        return format_local_datetime(dt, fmt=fmt, tz=tz)

    from app.routes import main_bp, auth_bp, jobs_bp, databases_bp, emails_bp, logs_bp, tools_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(jobs_bp, url_prefix="/jobs")
    app.register_blueprint(databases_bp, url_prefix="/databases")
    app.register_blueprint(emails_bp, url_prefix="/emails")
    app.register_blueprint(logs_bp, url_prefix="/logs")
    app.register_blueprint(tools_bp, url_prefix="/tools")

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()
        # Migrare: adaugă coloana scraper_library la jobs dacă lipsește (SQLite)
        if "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
            try:
                from sqlalchemy import text
                r = db.session.execute(text("PRAGMA table_info(jobs)"))
                cols = [row[1] for row in r.fetchall()]
                if "scraper_library" not in cols:
                    db.session.execute(text("ALTER TABLE jobs ADD COLUMN scraper_library VARCHAR(30) DEFAULT 'parsel'"))
                    db.session.commit()
            except Exception:
                db.session.rollback()
        from app.scheduler import init_scheduler
        init_scheduler(app)

    return app
