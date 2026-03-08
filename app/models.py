# -*- coding: utf-8 -*-
from datetime import datetime
from app import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DatabaseConnection(db.Model):
    __tablename__ = "database_connections"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    db_type = db.Column(db.String(20), nullable=False)  # postgres, mysql, sqlite, oracle
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    database = db.Column(db.String(120))
    username = db.Column(db.String(120))
    password = db.Column(db.String(255))
    extra = db.Column(db.Text)  # e.g. sqlite path, oracle DSN
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailConfig(db.Model):
    __tablename__ = "email_configs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    smtp_host = db.Column(db.String(255), nullable=False)
    smtp_port = db.Column(db.Integer, default=587)
    use_tls = db.Column(db.Boolean, default=True)
    username = db.Column(db.String(120))
    password = db.Column(db.String(255))
    from_email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.Text, nullable=False)
    scraper_library = db.Column(db.String(30), default="parsel")  # parsel, beautifulsoup, selenium
    active = db.Column(db.Boolean, default=True)
    schedule_cron = db.Column(db.String(120))  # e.g. "0 9 * * 1-5" lun-vineri 9:00
    schedule_label = db.Column(db.String(200))  # human: "Luni-Vineri 09:00"
    database_connection_id = db.Column(db.Integer, db.ForeignKey("database_connections.id"), nullable=True)
    verification_enabled = db.Column(db.Boolean, default=True)
    verification_sql = db.Column(db.Text)  # SELECT count(*) ... ; if count > 0 skip insert
    insert_sql = db.Column(db.Text)  # INSERT ...
    email_on_success = db.Column(db.Boolean, default=False)
    email_on_error = db.Column(db.Boolean, default=True)
    email_config_id = db.Column(db.Integer, db.ForeignKey("email_configs.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    database_connection = db.relationship("DatabaseConnection", backref="jobs")
    email_config = db.relationship("EmailConfig", backref="jobs")
    variables = db.relationship("JobVariable", backref="job", cascade="all, delete-orphan", order_by="JobVariable.order_index")


class JobVariable(db.Model):
    __tablename__ = "job_variables"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)  # e.g. price, discount
    extract_type = db.Column(db.String(20), nullable=False)  # xpath, css, constant
    selector = db.Column(db.Text)  # xpath or css selector; empty for constant
    constant_value = db.Column(db.Text)  # for constant
    format_type = db.Column(db.String(40))  # none, strip_percent, strip_currency, date_iso, date_sql, etc.
    order_index = db.Column(db.Integer, default=0)


class Log(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    job_name = db.Column(db.String(200))
    level = db.Column(db.String(20), nullable=False)  # info, success, error, email
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
