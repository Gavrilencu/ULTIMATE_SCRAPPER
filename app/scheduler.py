# -*- coding: utf-8 -*-
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


scheduler = BackgroundScheduler()
_app = None
_tz = None
_runner = None


def _get_timezone(app):
    """Returnează timezone-ul aplicației (Europe/Chisinau) pentru programare."""
    tz_name = app.config.get("TIMEZONE", "Europe/Chisinau")
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(tz_name)
    except ImportError:
        try:
            from backports.zoneinfo import ZoneInfo
            return ZoneInfo(tz_name)
        except ImportError:
            return None


def init_scheduler(app):
    global _app, _tz, _runner
    _app = app
    _tz = _get_timezone(app)
    def run_job_with_context(job_id):
        with _app.app_context():
            from app.job_runner import run_job
            run_job(job_id)
    _runner = run_job_with_context

    with app.app_context():
        from app.models import Job
        jobs = Job.query.filter_by(active=True).filter(Job.schedule_cron.isnot(None)).filter(Job.schedule_cron != "").all()
        for job in jobs:
            try:
                parts = job.schedule_cron.strip().split()
                if len(parts) >= 5:
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4],
                        timezone=_tz,
                    )
                    scheduler.add_job(_runner, trigger, args=[job.id], id=f"job_{job.id}", replace_existing=True)
            except Exception:
                pass
    if not scheduler.running:
        scheduler.start()


def add_job_schedule(job_id: int, cron_expr: str):
    if _runner is None:
        return
    parts = cron_expr.strip().split()
    if len(parts) < 5:
        return
    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
        timezone=_tz,
    )
    scheduler.add_job(_runner, trigger, args=[job_id], id=f"job_{job_id}", replace_existing=True)


def remove_job_schedule(job_id: int):
    try:
        scheduler.remove_job(f"job_{job_id}")
    except Exception:
        pass
