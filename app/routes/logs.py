# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required
from app.models import Log
from app.time_utils import format_local_datetime, get_app_timezone

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/")
@login_required
def list_logs():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    job_id = request.args.get("job_id", type=int)
    level = request.args.get("level")
    q = Log.query.order_by(Log.created_at.desc())
    if job_id:
        q = q.filter(Log.job_id == job_id)
    if level:
        q = q.filter(Log.level == level)
    pagination = q.paginate(page=page, per_page=per_page)
    return render_template("logs/list.html", logs=pagination.items, pagination=pagination, job_id=job_id, level=level)


@logs_bp.route("/api")
@login_required
def api_logs():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    job_id = request.args.get("job_id", type=int)
    level = request.args.get("level")
    q = Log.query.order_by(Log.created_at.desc())
    if job_id:
        q = q.filter(Log.job_id == job_id)
    if level:
        q = q.filter(Log.level == level)
    pagination = q.paginate(page=page, per_page=per_page)
    tz = get_app_timezone(current_app)
    items = [
        {
            "id": l.id,
            "job_id": l.job_id,
            "job_name": l.job_name,
            "level": l.level,
            "message": l.message,
            "details": l.details,
            "created_at": format_local_datetime(l.created_at, fmt="%Y-%m-%d %H:%M:%S", tz=tz) if l.created_at else None,
        }
        for l in pagination.items
    ]
    return jsonify({"items": items, "total": pagination.total, "pages": pagination.pages})
