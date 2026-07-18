"""Outbound email with an optional SMTP delivery path.

Without SMTP configuration, email is deliberately logged so development and
demo environments remain self-contained. Set SMTP_HOST to enable delivery.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("confusionlayer.mail")


def send_email(to: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    if host:
        message = EmailMessage()
        message["To"] = to
        message["From"] = os.getenv("SMTP_FROM", "no-reply@slate.local")
        message["Subject"] = subject
        message.set_content(body)
        port = int(os.getenv("SMTP_PORT", "587"))
        try:
            with smtplib.SMTP(host, port, timeout=10) as client:
                if os.getenv("SMTP_STARTTLS", "1") == "1":
                    client.starttls()
                username, password = os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD")
                if username and password:
                    client.login(username, password)
                client.send_message(message)
            logger.info("[smtp-email] delivered to=%s subject=%s", to, subject)
            return
        except (OSError, smtplib.SMTPException):
            logger.exception("[smtp-email] delivery failed; retaining development log")
    logger.info("[stub-email] to=%s subject=%s\n%s", to, subject, body)
    # Also print so it is visible in container logs during development.
    print(f"[stub-email] to={to} subject={subject}\n{body}", flush=True)
