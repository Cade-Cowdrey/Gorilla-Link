import os
from flask import render_template
from flask_mail import Message
from extensions import mail
from models import User, Department, Scholarship
from datetime import datetime

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstateconnect.edu")


# ----------------------------------
# Generic Email Utility
# ----------------------------------

def send_email(subject, recipients, html_body, text_body=None):
    """Send an email through Flask-Mail (SendGrid backend)."""
    msg = Message(subject, sender=DEFAULT_SENDER, recipients=recipients)
    msg.html = html_body
    if text_body:
        msg.body = text_body
    try:
        mail.send(msg)
        print(f"✅ Email sent to {recipients}: {subject}")
    except Exception as e:
        print(f"❌ Email error ({subject}): {e}")


# ----------------------------------
# Weekly Digest Emails
# ----------------------------------

def send_weekly_digest_students():
    """Send PSU-styled weekly digest to students with new scholarships & events."""
    users = User.query.all()
    scholarships = Scholarship.query.filter_by(is_active=True).limit(5).all()
    today = datetime.utcnow().strftime("%B %d, %Y")

    for user in users:
        if user.role and user.role.name.lower() == "student":
            html_body = render_template(
                "emails/digests/student_digest.html",
                user=user,
                scholarships=scholarships,
                date=today,
            )
            text_body = f"PittState Connect Weekly Digest - {today}\n\nYou have new scholarships and updates available."
            send_email(f"Gorilla Digest | {today}", [user.email], html_body, text_body)


def send_weekly_digest_alumni():
    """Send PSU-styled digest to alumni with mentorship, jobs, and campus news."""
    users = User.query.all()
    today = datetime.utcnow().strftime("%B %d, %Y")

    for user in users:
        if user.role and user.role.name.lower() == "alumni":
            html_body = render_template(
                "emails/digests/alumni_digest.html",
                user=user,
                date=today,
            )
            text_body = f"Gorilla Alumni Digest - {today}\n\nReconnect with PSU and view the latest alumni spotlights and opportunities."
            send_email(f"Gorilla Alumni Digest | {today}", [user.email], html_body, text_body)


def send_faculty_digest():
    """Send digest to faculty with scholarship recommendations and department stats."""
    departments = Department.query.all()
    today = datetime.utcnow().strftime("%B %d, %Y")

    for dept in departments:
        html_body = render_template(
            "emails/digests/faculty_digest.html",
            department=dept,
            date=today,
        )
        text_body = f"Faculty Digest - {dept.name}\n\nRecent student submissions, scholarships, and departmental analytics."
        send_email(f"Faculty Digest | {dept.name} | {today}", [DEFAULT_SENDER], html_body, text_body)


# ----------------------------------
# Scholarship Notifications
# ----------------------------------

def send_scholarship_confirmation(user, scholarship):
    """Notify user of successful scholarship application submission."""
    html_body = render_template(
        "emails/scholarships/confirmation.html",
        user=user,
        scholarship=scholarship,
    )
    text_body = f"Hi {user.first_name}, your application for {scholarship.title} has been received!"
    send_email(f"Confirmation: {scholarship.title} Submission", [user.email], html_body, text_body)


def send_scholarship_reminder(user, scholarship):
    """Remind users of approaching scholarship deadlines."""
    html_body = render_template(
        "emails/scholarships/reminder.html",
        user=user,
        scholarship=scholarship,
    )
    text_body = f"Reminder: {scholarship.title} deadline is approaching soon."
    send_email(f"Deadline Reminder: {scholarship.title}", [user.email], html_body, text_body)
