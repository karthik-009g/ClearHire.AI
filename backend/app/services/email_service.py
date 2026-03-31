"""Email delivery service for matched job digest."""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.utils.config import settings


class EmailService:
    def is_configured(self) -> bool:
        return bool(
            settings.smtp_host
            and settings.smtp_username
            and settings.smtp_password
            and settings.smtp_sender_email
        )

    def send_html_email(self, to_email: str, subject: str, html_body: str) -> None:
        if not self.is_configured():
            raise RuntimeError("SMTP is not configured")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_sender_email
        message["To"] = to_email
        message.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_sender_email, [to_email], message.as_string())
