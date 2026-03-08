# -*- coding: utf-8 -*-
from app import db
from app.models import Job, Log
from app.scraper import fetch_page, extract_from_page
from app.db_runner import get_connection, run_count_query, run_insert
from app.email_sender import send_email


def run_job(job_id: int) -> None:
    job = Job.query.get(job_id)
    if not job:
        return
    job_name = job.name
    log_info = lambda msg, details=None: _log(job_id, job_name, "info", msg, details)
    log_success = lambda msg, details=None: _log(job_id, job_name, "success", msg, details)
    log_error = lambda msg, details=None: _log(job_id, job_name, "error", msg, details)
    log_email = lambda msg, details=None: _log(job_id, job_name, "email", msg, details)

    try:
        library = getattr(job, "scraper_library", None) or "parsel"
        log_info("Pornire job", job.url)
        html, err = fetch_page(job.url, library=library)
        if err:
            log_error("Eroare la descărcarea paginii", err)
            _try_email(job, False, f"Eroare: {err}")
            return

        variables = {v.name: "" for v in job.variables}
        extracted = extract_from_page(html, job.variables, library=library)
        variables.update(extracted)
        log_info("Variabile extrase", str(extracted))

        if job.database_connection_id and job.verification_enabled and (job.verification_sql or "").strip():
            conn = get_connection(job.database_connection)
            try:
                count = run_count_query(conn, job.verification_sql.strip(), variables)
                if count > 0:
                    log_info("Verificare: există deja înregistrări (count > 0), inserarea este omisă.", str(count))
                    _try_email(job, True, "Inserare omisă (verificare count > 0).")
                    return
            except Exception as e:
                log_error("Eroare la verificare SQL", str(e))
                _try_email(job, False, str(e))
                return
            finally:
                conn.close()

        if job.database_connection_id and (job.insert_sql or "").strip():
            conn = get_connection(job.database_connection)
            try:
                run_insert(conn, job.insert_sql.strip(), variables)
                log_success("Inserare reușită", job.insert_sql[:200])
                _try_email(job, True, "Inserare reușită.")
            except Exception as e:
                log_error("Eroare la inserare", str(e))
                _try_email(job, False, str(e))
            finally:
                conn.close()
        else:
            log_success("Job finalizat (fără inserare)", "")
            _try_email(job, True, "Job finalizat.")
    except Exception as e:
        log_error("Eroare neașteptată", str(e))
        _try_email(job, False, str(e))


def _log(job_id, job_name, level, message, details=None):
    entry = Log(job_id=job_id, job_name=job_name, level=level, message=message, details=details or "")
    db.session.add(entry)
    db.session.commit()


def _try_email(job, success, message):
    if success and not job.email_on_success:
        return
    if not success and not job.email_on_error:
        return
    if not job.email_config_id:
        return
    config = job.email_config
    if not config:
        return
    subject = f"[Scrapper] {'Succes' if success else 'Eroare'} - {job.name}"
    body = f"Job: {job.name}\nRezultat: {'Succes' if success else 'Eroare'}\nDetalii: {message}"
    ok, err = send_email(config, [config.from_email], subject, body)
    _log(job.id, job.name, "email", "Email trimis" if ok else f"Eroare email: {err}", body if ok else err)
