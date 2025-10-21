import os
import requests
from flask import current_app
from flask_mail import Message
from extensions import mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_email(to, subject, html_body=None, text_body=None, sender=None):
    sender = sender or current_app.config.get("MAIL_DEFAULT_SENDER")
    if SENDGRID_API_KEY:
        url = "https://api.sendgrid.com/v3/mail/send"
        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": sender},
            "subject": subject,
            "content": []
        }
        if text_body:
            payload["content"].append({"type": "text/plain", "value": text_body})
        if html_body:
            payload["content"].append({"type": "text/html", "value": html_body})

        headers = {"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"}
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        return True
    else:
        msg = Message(subject=subject, recipients=[to], sender=sender, body=text_body)
        if html_body:
            msg.html = html_body
        mail.send(msg)
        return True
