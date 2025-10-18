from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, mail
from utils.mail_util import (
    send_verification_email,
    send_reset_password_email,
    send_reactivation_email,
    send_reactivated_email,
    send_account_deleted_email,
    send_farewell_email
)
from models import User
import datetime

auth = Blueprint("auth", __name__, template_folder="templates")

# Utility: generate signed tokens
def generate_token(email, salt):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=salt)

def confirm_token(token, salt, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
    except (SignatureExpired, BadSignature):
        return None
    return email


# ----------------------------------------------
# 🔐 AUTH & REGISTRATION
# ----------------------------------------------
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("That email is already registered.", "warning")
            return redirect(url_for("auth.register"))

        hashed_pw = generate_password_hash(password, method="sha256")
        user = User(name=name, email=email, password=hashed_pw, verified=False)
        db.session.add(user)
        db.session.commit()

        token = generate_token(user.email, "email-confirm")
        send_verification_email(user, token)
        flash("Registration successful! Please check your email to verify your account.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not user.verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash("Welcome back, Gorilla!", "success")
        return redirect(url_for("core.home"))

    return render_template("auth/login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("core.home"))


# ----------------------------------------------
# 📧 EMAIL VERIFICATION
# ----------------------------------------------
@auth.route("/verify/<token>")
def verify_email(token):
    email = confirm_token(token, "email-confirm")
    if not email:
        flash("Verification link is invalid or expired.", "danger")
        return redirect(url_for("auth.verify_failed"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("auth.verify_failed"))

    if user.verified:
        flash("Your account is already verified.", "info")
        return redirect(url_for("auth.login"))

    user.verified = True
    db.session.commit()
    flash("Your account has been verified!", "success")
    return redirect(url_for("auth.verify_success"))


@auth.route("/verify-success")
def verify_success():
    return render_template("auth/verify_success.html")


@auth.route("/verify-failed")
def verify_failed():
    return render_template("auth/verify_failed.html")


@auth.route("/verify-resent")
def verify_resent():
    return render_template("auth/verify_resent.html")


@auth.route("/resend-verification")
@login_required
def resend_verification():
    token = generate_token(current_user.email, "email-confirm")
    send_verification_email(current_user, token)
    flash("A new verification link has been sent to your email.", "info")
    return redirect(url_for("auth.verify_resent"))


# ----------------------------------------------
# 🔑 PASSWORD RESET
# ----------------------------------------------
@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with that email.", "warning")
            return redirect(url_for("auth.forgot_password"))

        token = generate_token(email, "password-reset")
        send_reset_password_email(user, token)
        flash("Password reset link sent! Check your email.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = confirm_token(token, "password-reset")
    if not email:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_pw = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(new_pw, method="sha256")
        db.session.commit()
        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for("auth.reset_success"))

    return render_template("auth/reset_password.html")


@auth.route("/reset-success")
def reset_success():
    return render_template("auth/reset_success.html")


# ----------------------------------------------
# ⚙️ ACCOUNT STATUS MANAGEMENT
# ----------------------------------------------
@auth.route("/deactivate-account")
@login_required
def deactivate_account():
    current_user.active = False
    db.session.commit()

    token = generate_token(current_user.email, "reactivate-account")
    send_reactivation_email(current_user, token)
    logout_user()

    flash("Your account has been deactivated. A reactivation link was emailed to you.", "info")
    return redirect(url_for("auth.deactivated"))


@auth.route("/deactivated")
def deactivated():
    return render_template("auth/deactivated.html")


@auth.route("/reactivate/<token>")
def reactivate_account(token):
    email = confirm_token(token, "reactivate-account")
    if not email:
        flash("Invalid or expired reactivation link.", "danger")
        return redirect(url_for("auth.deactivated"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("auth.deactivated"))

    user.active = True
    db.session.commit()
    send_reactivated_email(user)
    flash("Your account has been successfully reactivated!", "success")
    return redirect(url_for("auth.reactivated"))


@auth.route("/reactivated")
def reactivated():
    return render_template("auth/reactivated.html")


@auth.route("/delete-account")
@login_required
def delete_account():
    send_account_deleted_email(current_user)
    send_farewell_email(current_user)

    db.session.delete(current_user)
    db.session.commit()

    flash("Your account has been permanently deleted.", "info")
    return redirect(url_for("auth.deleted"))


@auth.route("/deleted")
def deleted():
    return render_template("auth/deleted.html")


# ----------------------------------------------
# 🗂️ NOTIFICATION INDEX PREVIEW
# ----------------------------------------------
@auth.route("/notifications-index")
@login_required
def notifications_index():
    """Preview all auth and system notification templates."""
    return render_template("auth/notifications_index.html")
