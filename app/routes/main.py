# -*- coding: utf-8 -*-
from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user
from app.routes.auth import has_any_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if not has_any_user():
        return redirect(url_for("auth.setup"))
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("jobs.list_jobs"))
