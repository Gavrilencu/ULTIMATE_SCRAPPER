# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models import EmailConfig
from app.email_sender import send_email

emails_bp = Blueprint("emails", __name__)


@emails_bp.route("/")
@login_required
def list_configs():
    configs = EmailConfig.query.order_by(EmailConfig.name).all()
    return render_template("emails/list.html", configs=configs)


@emails_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_config():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        smtp_host = (request.form.get("smtp_host") or "").strip()
        smtp_port = request.form.get("smtp_port") or "587"
        use_tls = request.form.get("use_tls") == "1"
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        from_email = (request.form.get("from_email") or "").strip()
        if not name or not smtp_host or not from_email:
            flash("Nume, host SMTP și adresa expeditor sunt obligatorii.", "error")
            return redirect(request.referrer or url_for("emails.list_configs"))
        cfg = EmailConfig(
            name=name, smtp_host=smtp_host, smtp_port=int(smtp_port), use_tls=use_tls,
            username=username or None, password=password or None, from_email=from_email
        )
        db.session.add(cfg)
        db.session.commit()
        flash("Configurare email adăugată.", "success")
        return redirect(url_for("emails.list_configs"))
    return render_template("emails/edit.html", config=None)


@emails_bp.route("/<int:config_id>/edit", methods=["GET", "POST"])
@login_required
def edit_config(config_id):
    config = EmailConfig.query.get_or_404(config_id)
    if request.method == "POST":
        config.name = (request.form.get("name") or "").strip()
        config.smtp_host = (request.form.get("smtp_host") or "").strip()
        config.smtp_port = int(request.form.get("smtp_port") or 587)
        config.use_tls = request.form.get("use_tls") == "1"
        config.username = (request.form.get("username") or "").strip() or None
        if request.form.get("password"):
            config.password = request.form.get("password")
        config.from_email = (request.form.get("from_email") or "").strip()
        db.session.commit()
        flash("Configurare actualizată.", "success")
        return redirect(url_for("emails.list_configs"))
    return render_template("emails/edit.html", config=config)


@emails_bp.route("/<int:config_id>/test", methods=["POST"])
@login_required
def test_config(config_id):
    config = EmailConfig.query.get_or_404(config_id)
    to_email = (request.form.get("to_email") or request.json.get("to_email") or config.from_email).strip()
    ok, err = send_email(config, [to_email], "Test Scrapper Ultimate", "Acesta este un email de test.")
    if ok:
        return jsonify({"ok": True, "message": "Email de test trimis."})
    return jsonify({"ok": False, "message": err}), 400


@emails_bp.route("/<int:config_id>/delete", methods=["POST"])
@login_required
def delete_config(config_id):
    config = EmailConfig.query.get_or_404(config_id)
    db.session.delete(config)
    db.session.commit()
    flash("Configurare ștearsă.", "success")
    return redirect(url_for("emails.list_configs"))
