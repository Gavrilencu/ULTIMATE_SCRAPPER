# -*- coding: utf-8 -*-
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models import Job, JobVariable, DatabaseConnection, EmailConfig
from app.scheduler import add_job_schedule, remove_job_schedule
from app.job_runner import run_job
from app.scraper import LIBRARIES

jobs_bp = Blueprint("jobs", __name__)


def cron_from_form():
    # form: schedule_weekdays (1-5), schedule_time "09:00"
    weekdays = request.form.getlist("schedule_weekdays")
    time_str = request.form.get("schedule_time") or "09:00"
    if not weekdays:
        return None, None
    try:
        h, m = map(int, time_str.split(":")[:2])
    except Exception:
        h, m = 9, 0
    # cron: minute hour day month day_of_week
    dow = ",".join(sorted(weekdays)) if weekdays else "*"
    cron = f"{m} {h} * * {dow}"
    label = f"Luni-Duminică {h:02d}:{m:02d}"
    days_ro = {"1": "Luni", "2": "Marți", "3": "Miercuri", "4": "Joi", "5": "Vineri", "6": "Sâmbătă", "0": "Duminică"}
    label = ", ".join(days_ro.get(d, d) for d in sorted(weekdays)) + f" {h:02d}:{m:02d}"
    return cron, label


@jobs_bp.route("/")
@login_required
def list_jobs():
    jobs = Job.query.order_by(Job.updated_at.desc()).all()
    return render_template("jobs/list.html", jobs=jobs)


@jobs_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_job():
    if request.method == "POST":
        return _save_job(None)
    db_connections = DatabaseConnection.query.all()
    email_configs = EmailConfig.query.all()
    return render_template("jobs/edit.html", job=None, job_variables=[], db_connections=db_connections, email_configs=email_configs, libraries=LIBRARIES)


@jobs_bp.route("/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        return _save_job(job)
    db_connections = DatabaseConnection.query.all()
    email_configs = EmailConfig.query.all()
    job_variables = [{"name": v.name, "extract_type": v.extract_type, "selector": v.selector or "", "constant_value": v.constant_value or "", "format_type": v.format_type or "none", "order_index": v.order_index} for v in job.variables]
    return render_template("jobs/edit.html", job=job, job_variables=job_variables, db_connections=db_connections, email_configs=email_configs, libraries=LIBRARIES)


def _save_job(job):
    name = (request.form.get("name") or "").strip()
    url = (request.form.get("url") or "").strip()
    if not name or not url:
        flash("Numele și URL-ul sunt obligatorii.", "error")
        return redirect(request.referrer or url_for("jobs.list_jobs"))
    active = request.form.get("active") == "1"
    verification_enabled = request.form.get("verification_enabled") == "1"
    verification_sql = request.form.get("verification_sql") or ""
    insert_sql = request.form.get("insert_sql") or ""
    db_conn_id = request.form.get("database_connection_id")
    email_config_id = request.form.get("email_config_id")
    email_on_success = request.form.get("email_on_success") == "1"
    email_on_error = request.form.get("email_on_error") == "1"
    scraper_library = (request.form.get("scraper_library") or "parsel").strip()

    cron, label = cron_from_form()

    if job is None:
        job = Job(
            name=name, url=url, scraper_library=scraper_library, active=active,
            schedule_cron=cron, schedule_label=label,
            verification_enabled=verification_enabled, verification_sql=verification_sql, insert_sql=insert_sql,
            database_connection_id=int(db_conn_id) if db_conn_id else None,
            email_config_id=int(email_config_id) if email_config_id else None,
            email_on_success=email_on_success, email_on_error=email_on_error,
        )
        db.session.add(job)
        db.session.flush()
    else:
        job.name = name
        job.url = url
        job.scraper_library = scraper_library
        job.active = active
        job.schedule_cron = cron
        job.schedule_label = label
        job.verification_enabled = verification_enabled
        job.verification_sql = verification_sql
        job.insert_sql = insert_sql
        job.database_connection_id = int(db_conn_id) if db_conn_id else None
        job.email_config_id = int(email_config_id) if email_config_id else None
        job.email_on_success = email_on_success
        job.email_on_error = email_on_error

    # Variables JSON: [{"name","extract_type","selector","constant_value","format_type","order_index"}]
    vars_json = request.form.get("variables_json")
    if vars_json:
        try:
            JobVariable.query.filter_by(job_id=job.id).delete()
            for i, v in enumerate(json.loads(vars_json)):
                var = JobVariable(
                    job_id=job.id,
                    name=(v.get("name") or "").strip(),
                    extract_type=v.get("extract_type") or "xpath",
                    selector=(v.get("selector") or "").strip(),
                    constant_value=(v.get("constant_value") or "").strip(),
                    format_type=v.get("format_type") or "none",
                    order_index=i,
                )
                if var.name:
                    db.session.add(var)
        except Exception:
            pass

    db.session.commit()

    if job.schedule_cron and job.active:
        add_job_schedule(job.id, job.schedule_cron)
    else:
        remove_job_schedule(job.id)

    flash("Job salvat.", "success")
    return redirect(url_for("jobs.list_jobs"))


@jobs_bp.route("/<int:job_id>/toggle", methods=["POST"])
@login_required
def toggle_job(job_id):
    job = Job.query.get_or_404(job_id)
    job.active = not job.active
    db.session.commit()
    if job.active and job.schedule_cron:
        add_job_schedule(job.id, job.schedule_cron)
    else:
        remove_job_schedule(job.id)
    return jsonify({"active": job.active})


@jobs_bp.route("/<int:job_id>/run", methods=["POST"])
@login_required
def run_now(job_id):
    job = Job.query.get_or_404(job_id)
    run_job(job.id)
    flash("Job rulat.", "success")
    return redirect(url_for("jobs.list_jobs"))


@jobs_bp.route("/<int:job_id>/delete", methods=["POST"])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    remove_job_schedule(job.id)
    db.session.delete(job)
    db.session.commit()
    flash("Job șters.", "success")
    return redirect(url_for("jobs.list_jobs"))
