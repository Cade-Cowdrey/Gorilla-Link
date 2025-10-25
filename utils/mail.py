# utils/mail.py
from __future__ import annotations

import os
from typing import Dict, Optional
from flask import Flask, render_template
from flask_mail import Mail, Message
from tenacity import retry, stop_after_attempt, wait_exponential

mail = Mail()

def init_mail(app: Flask) -> None:
    app.config.setdefault("MAIL_SERVER", os.environ.get("MAIL_SERVER", "localhost"))
    app.config.setdefault("MAIL_PORT", int(os.environ.get("MAIL_PORT", "25")))
    app.config.setdefault("MAIL_USE_TLS", os.environ.get("MAIL_USE_TLS", "false").lower() == "true")
    app.config.setdefault("MAIL_USE_SSL", os.environ.get("MAIL_USE_SSL", "false").lower() == "true")
    app.config.setdefault("MAIL_USERNAME", os.environ.get("MAIL_USERNAME"))
    app.config.setdefault("MAIL_PASSWORD", os.environ.get("MAIL_PASSWORD"))
    app.config.setdefault("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_DEFAULT_SENDER", "noreply@pittstate.edu"))
    mail.init_app(app)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def send_templated_email(
    subject: str,
    recipients: list[str],
    template: str,
    context: Optional[Dict] = None,
    bcc: Optional[list[str]] = None,
    attachments: Optional[list[tuple[str, str, bytes]]] = None,
) -> None:
    """
    template: base name without extension, resolves to:
      templates/emails/{template}.html and templates/emails/{template}.txt
    """
    context = context or {}
    html = render_template(f"emails/{template}.html", **context)
    text = render_template(f"emails/{template}.txt", **context)

    msg = Message(subject=subject, recipients=recipients, bcc=bcc or [])
    msg.body = text
    msg.html = html

    if attachments:
        for fname, mimetype, data in attachments:
            msg.attach(filename=fname, content_type=mimetype, data=data)

    mail.send(msg)
