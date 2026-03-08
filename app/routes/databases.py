# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models import DatabaseConnection
from app.db_runner import get_connection

databases_bp = Blueprint("databases", __name__)


@databases_bp.route("/")
@login_required
def list_connections():
    connections = DatabaseConnection.query.order_by(DatabaseConnection.name).all()
    return render_template("databases/list.html", connections=connections)


@databases_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_connection():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        db_type = request.form.get("db_type") or "sqlite"
        host = (request.form.get("host") or "").strip()
        port = request.form.get("port")
        database = (request.form.get("database") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        extra = (request.form.get("extra") or "").strip()
        if not name:
            flash("Numele conexiunii este obligatoriu.", "error")
            return redirect(request.referrer or url_for("databases.list_connections"))
        port = int(port) if port else (5432 if db_type == "postgres" else 3306 if db_type == "mysql" else 1521)
        conn = DatabaseConnection(
            name=name, db_type=db_type, host=host or None, port=port or None,
            database=database or None, username=username or None, password=password or None, extra=extra or None
        )
        db.session.add(conn)
        db.session.commit()
        flash("Conexiune adăugată.", "success")
        return redirect(url_for("databases.list_connections"))
    return render_template("databases/edit.html", connection=None)


@databases_bp.route("/<int:conn_id>/edit", methods=["GET", "POST"])
@login_required
def edit_connection(conn_id):
    conn = DatabaseConnection.query.get_or_404(conn_id)
    if request.method == "POST":
        conn.name = (request.form.get("name") or "").strip()
        conn.db_type = request.form.get("db_type") or conn.db_type
        conn.host = (request.form.get("host") or "").strip() or None
        port = request.form.get("port")
        conn.port = int(port) if port else None
        conn.database = (request.form.get("database") or "").strip() or None
        conn.username = (request.form.get("username") or "").strip() or None
        if request.form.get("password"):
            conn.password = request.form.get("password")
        conn.extra = (request.form.get("extra") or request.form.get("oracle_dsn") or "").strip() or None
        db.session.commit()
        flash("Conexiune actualizată.", "success")
        return redirect(url_for("databases.list_connections"))
    return render_template("databases/edit.html", connection=conn)


@databases_bp.route("/<int:conn_id>/test", methods=["POST"])
@login_required
def test_connection(conn_id):
    conn = DatabaseConnection.query.get_or_404(conn_id)
    try:
        c = get_connection(conn)
        c.close()
        return jsonify({"ok": True, "message": "Conexiune reușită."})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400


@databases_bp.route("/<int:conn_id>/delete", methods=["POST"])
@login_required
def delete_connection(conn_id):
    conn = DatabaseConnection.query.get_or_404(conn_id)
    db.session.delete(conn)
    db.session.commit()
    flash("Conexiune ștearsă.", "success")
    return redirect(url_for("databases.list_connections"))
