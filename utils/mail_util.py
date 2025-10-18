from flask_mail import Message
from flask import render_template, url_for, current_app
from extensions import mail
from datetime import datetime

# ------------------------------------------------
# PSU-BRANDED EMAIL UTILITIES
# ------------------------------------------------

def send_verification_email(user, token):
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    html = render_template(
        'emails/account_verification_email.html',
        user=user,
        verify_url=verify_url,
        current_year=datetime.now().year
    )
    msg = Message(
        subject="Verify Your PittState-Connect Account 🦍",
        recipients=[user.email],
        html=html,
        sender="support@pittstateconnect.com"
    )
    mail.send(msg)


def send_reset_password_email(user, token):
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    html = render_template(
        'emails/reset_password_email.html',
        user=user,
        reset_url=reset_url,
        current_year=datetime.now().year
    )
    msg = Message(
        subject="Reset Your Password | PittState-Connect",
        recipients=[user.email],
        html=html,
        sender="support@pittstateconnect.com"
    )
    mail.send(msg)


def send_reactivation_email(user, token):
    reactivate_url = url_for('auth.reactivate_account', token=token, _external=True)
    html = render_template(
        'emails/reactivation_email.html',
        user=user,
        reactivate_url=reactivate_url,
        current_year=datetime.now().year
    )
    msg = Message(
        subject="Reactivate Your Account | PittState-Connect",
        recipients=[user.email],
        html=html,
        sender="support@pittstateconnect.com"
    )
    mail.send(msg)


def send_reactivated_email(user):
    html = render_template(
        'emails/reactivated_email.html',
        user=user,
        current_year=datetime.now().year
    )
    msg = Message(
        subject="Welcome Back to PittState-Connect 🦍",
        recipients=[user.email],
        html=html,
        sender="support@pittstateconnect.com"
    )
    mail.send(msg)


def send_account_deleted_email(user):
    html = render_template(
        'emails/account_deleted_email.html',
        user=user,
        current_year=datetime.now().year
    )
    msg = Message(
        subject="Your PittState-Connect Account Has Been Deleted 🕊️",
        recipients=[user.email],
        html=html,
        sender="support@pittstateconnect.com"
    )
    mail.send(msg)


def send_farewell_email(user):
    html = render_template(
        'emails/farewell_email.html',
        user=user,
        current_year=datetime.now().year
    )
    msg = Message(
        subject="Farewell from PittState-Connect ❤️",
        recipients=[user.email],
        html=html,
        sender="support@pittstateconnect.com"
    )
    mail.send(msg)
