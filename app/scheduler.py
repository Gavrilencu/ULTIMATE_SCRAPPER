# -*- coding: utf-8 -*-
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


scheduler = BackgroundScheduler()


def init_scheduler(app):
    with app.app_context():
        from app.models import Job
        from app.job_runner import run_job
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
                    )
                    scheduler.add_job(run_job, trigger, args=[job.id], id=f"job_{job.id}", replace_existing=True)
            except Exception:
                pass
    scheduler.start()


def add_job_schedule(job_id: int, cron_expr: str):
    from app.job_runner import run_job
    parts = cron_expr.strip().split()
    if len(parts) < 5:
        return
    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )
    scheduler.add_job(run_job, trigger, args=[job_id], id=f"job_{job_id}", replace_existing=True)


def remove_job_schedule(job_id: int):
    try:
        scheduler.remove_job(f"job_{job_id}")
    except Exception:
        pass
