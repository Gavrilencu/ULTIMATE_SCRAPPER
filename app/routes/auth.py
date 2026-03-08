# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.auth_utils import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)


def has_any_user():
    return User.query.first() is not None


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    if has_any_user():
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            flash("Completați utilizatorul și parola.", "error")
            return render_template("setup.html")
        if len(password) < 6:
            flash("Parola trebuie să aibă cel puțin 6 caractere.", "error")
            return render_template("setup.html")
        user = User(username=username, password_hash=hash_password(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Cont creat. Bine ați venit!", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("setup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not has_any_user():
        return redirect(url_for("auth.setup"))
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()
        if user and verify_password(password, user.password_hash):
            login_user(user)
            next_url = request.args.get("next") or url_for("main.dashboard")
            return redirect(next_url)
        flash("Utilizator sau parolă incorectă.", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
