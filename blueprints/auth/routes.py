# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Authentication Routes (Register, Login, Verify, Reset)
# ---------------------------------------------------------
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from extensions import db
from models import User
from utils.mail_util import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email
)
from werkzeug.security import generate_password_hash, check_password_hash
import os

auth = Blueprint("auth", __name__, template_folder="templates")


# ---------------------------------------------------------
# 🔐 Helper: Generate / Verify Secure Tokens
# ---------------------------------------------------------
def generate_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="email-confirm")


def verify_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = s.loads(token, salt="email-confirm", max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None


# ---------------------------------------------------------
# 🧍‍♂️ Register
# ---------------------------------------------------------
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email").lower()
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "warning")
            return redirect(url_for("auth.register"))

        hashed_pw = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_pw, is_verified=False)

        db.session.add(new_user)
        db.session.commit()

        # Generate verification token
        token = generate_token(new_user.email)
        send_verification_email(new_user, token)

        flash("✅ Registration successful! Please check your email to verify your account.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ---------------------------------------------------------
# 🔓 Login
# ---------------------------------------------------------
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").lower()
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash("Please verify your email before logging in.", "warning")
                return redirect(url_for("auth.login"))
            login_user(user)
            flash("Welcome back, Gorilla!", "success")
            return redirect(url_for("core.home"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


# ---------------------------------------------------------
# 🚪 Logout
# ---------------------------------------------------------
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------
# ✅ Email Verification
# ---------------------------------------------------------
@auth.route("/verify/<token>")
def verify_email(token):
    email = verify_token(token)
    if not email:
        flash("Verification link expired or invalid.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user and not user.is_verified:
        user.is_verified = True
        db.session.commit()
        send_welcome_email(user)
        flash("✅ Your account has been verified. Welcome to PittState-Connect!", "success")
    else:
        flash("Your account is already verified.", "info")

    return redirect(url_for("auth.login"))


# ---------------------------------------------------------
# 🔐 Password Reset Request
# ---------------------------------------------------------
@auth.route("/reset-password-request", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email").lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_token(user.email)
            send_password_reset_email(user, token)
            flash("Password reset instructions have been sent to your email.", "info")
        else:
            flash("No account found with that email.", "warning")

        return redirect(url_for("auth.login"))

    return render_template("auth/reset_request.html")


# ---------------------------------------------------------
# 🔑 Password Reset (Token)
# ---------------------------------------------------------
@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_token(token)
    if not email:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.reset_request"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("auth.reset_request"))

    if request.method == "POST":
        new_password = request.form.get("password")
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("✅ Your password has been updated. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
