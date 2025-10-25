# utils/mail.py
from __future__ import annotations
import os
from typing import Iterable, Optional
from flask_mail import Mail, Message
from flask import current_app

_mail: Optional[Mail] = None

def init_mail(app):
    """
    Initialize Flask-Mail with sensible production defaults.
    Safe to call multiple times; will reuse instance.
    """
    global _mail
    if _mail:
        return _mail

    app.config.setdefault("MAIL_SERVER", os.getenv("MAIL_SERVER", "smtp.sendgrid.net"))
    app.config.setdefault("MAIL_PORT", int(os.getenv("MAIL_PORT", "587")))
    app.config.setdefault("MAIL_USE_TLS", True)
    app.config.setdefault("MAIL_USERNAME", os.getenv("MAIL_USERNAME", "apikey"))
    app.config.setdefault("MAIL_PASSWORD", os.getenv("MAIL_PASSWORD", ""))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstate.edu"))
    app.config.setdefault("MAIL_SUPPRESS_SEND", app.config.get("TESTING", False))
    _mail = Mail(app)
    return _mail

def send_email(
    subject: str,
    recipients: Iterable[str],
    html: str | None = None,
    body: str | None = None,
    bcc: Iterable[str] | None = None,
    attachments: list[tuple[str, str, bytes]] | None = None,
    reply_to: str | None = None,
):
    """
    Production-friendly email utility with HTML + attachments.
    """
    mail = _mail or init_mail(current_app)
    msg = Message(
        subject=subject,
        recipients=list(recipients),
        bcc=list(bcc) if bcc else None,
        reply_to=reply_to or current_app.config.get("MAIL_REPLY_TO"),
    )
    if body:
        msg.body = body
    if html:
        msg.html = html
    if attachments:
        for filename, mimetype, data in attachments:
            msg.attach(filename=filename, content_type=mimetype, data=data)

    mail.send(msg)
