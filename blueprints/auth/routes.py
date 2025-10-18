# ---------------------------------------------
#  PittState-Connect / Gorilla-Link
#  AUTH BLUEPRINT ROUTES — FINAL PSU EDITION
# ---------------------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from models import db, User
from utils.mail_util import (
    send_verification_email,
    send_reset_email,
    send_verified_success_email
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -----------------------------
# Helper — Token Serializer
# -----------------------------
def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


# -----------------------------
# Register New Account
# -----------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").lower()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "warning")
            return redirect(url_for("auth.login"))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=generate_password_hash(password),
            verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        # Send verification link
        serializer = get_serializer()
        token = serializer.dumps(email, salt="email-confirm-salt")
        confirm_url = url_for("auth.confirm_email", token=token, _external=True)
        send_verification_email(email, confirm_url)

        flash("Account created! Check your email to verify before logging in.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# -----------------------------
# Login
# -----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not user.verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for("auth.resend_verification"))

        login_user(user, remember=True)
        flash("Welcome back!", "success")
        return redirect(url_for("feed.dashboard"))

    return render_template("auth/login.html")


# -----------------------------
# Logout
# -----------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("core.home"))


# -----------------------------
# Confirm Email
# -----------------------------
@auth_bp.route("/confirm/<token>")
def confirm_email(token):
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=3600)
    except SignatureExpired:
        flash("Your confirmation link has expired. Please resend.", "warning")
        return redirect(url_for("auth.resend_verification"))
    except BadSignature:
        flash("Invalid confirmation token.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Account not found.", "danger")
        return redirect(url_for("auth.register"))

    if user.verified:
        return render_template("auth/confirm_success.html", already_verified=True)

    user.verified = True
    db.session.commit()
    send_verified_success_email(email)
    return render_template("auth/confirm_success.html", already_verified=False)


# -----------------------------
# Resend Verification
# -----------------------------
@auth_bp.route("/resend_verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with that email.", "danger")
            return redirect(url_for("auth.resend_verification"))

        if user.verified:
            flash("This account is already verified. Please log in.", "info")
            return redirect(url_for("auth.login"))

        serializer = get_serializer()
        token = serializer.dumps(email, salt="email-confirm-salt")
        confirm_url = url_for("auth.confirm_email", token=token, _external=True)
        send_verification_email(email, confirm_url)
        return render_template("auth/email_sent.html")

    return render_template("auth/resend_verification.html")


# -----------------------------
# Password Reset Request
# -----------------------------
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        user = User.query.filter_by(email=email).first()

        if user:
            serializer = get_serializer()
            token = serializer.dumps(email, salt="password-reset-salt")
            reset_url = url_for("auth.reset_with_token", token=token, _external=True)
            send_reset_email(email, reset_url)
            return render_template("auth/email_sent.html")

        flash("No account found with that email.", "danger")
    return render_template("auth/reset_request.html")


# -----------------------------
# Password Reset (Token Page)
# -----------------------------
@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_with_token(token):
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.reset_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.reset_with_token", token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            flash("Password reset successfully. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/reset_token.html")
