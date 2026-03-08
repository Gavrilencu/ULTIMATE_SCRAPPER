# -*- coding: utf-8 -*-
"""
Trimitere email: MIMEMultipart + MIMEText, SMTP cu sau fără TLS.
Pentru Exchange (ex: exchange.mobiasbanca.md:5525) folosiți TLS dezactivat.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models import EmailConfig


def send_email(config: EmailConfig, to_emails: list, subject: str, body: str) -> tuple[bool, str]:
    to_emails = [e.strip() for e in to_emails if e and e.strip()]
    if not to_emails:
        return False, "Nicio adresă de email destinatar."

    # Creare mesaj (MIMEMultipart + MIMEText)
    msg = MIMEMultipart()
    msg["From"] = config.from_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            if config.use_tls:
                server.starttls()
            if config.username:
                server.login(config.username, config.password or "")
            server.sendmail(config.from_email, to_emails, msg.as_string())
        return True, ""
    except Exception as e:
        return False, str(e)
