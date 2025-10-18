"""
blueprints/auth/routes_password_reset.py
----------------------------------------
Handles password reset (forgot + reset) for PittState-Connect.
Only PSU (.pittstate.edu) emails are allowed.
----------------------------------------
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from datetime import datetime
from models import db, User
from utils.mail_util import send_email

password_bp = Blueprint("password", __name__, template_folder="templates", static_folder="static")


# ---------------------------------------------------------------------
# 🔑 Config helper
# ---------------------------------------------------------------------
def get_serializer():
    """Initialize the URL serializer for secure token generation."""
    secret_key = current_app.config.get("SECRET_KEY")
    return URLSafeTimedSerializer(secret_key)


# ---------------------------------------------------------------------
# 📨 Forgot Password Route
# ---------------------------------------------------------------------
@password_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Accepts a PSU email and sends a time-limited reset link to the user.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        # Must be a Pitt State email
        if not email.endswith(".pittstate.edu"):
            flash("❌ Only official Pittsburg State University emails are allowed.", "danger")
            return redirect(url_for("password.forgot_password"))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("We couldn’t find an account with that email.", "warning")
            return redirect(url_for("password.forgot_password"))

        try:
            serializer = get_serializer()
            token = serializer.dumps(email, salt="password-reset-salt")

            reset_url = url_for("password.reset_password", token=token, _external=True)
            html_body = render_template(
                "emails/password_reset.html",
                reset_url=reset_url,
                user=user,
                current_year=datetime.now().year,
            )

            send_email(
                subject="Password Reset | PittState-Connect",
                recipients=[email],
                html_body=html_body,
            )

            flash("✅ A password reset link has been sent to your PSU email.", "success")
            current_app.logger.info(f"[PASSWORD RESET REQUEST] Sent reset link to {email}")

        except Exception as e:
            current_app.logger.error(f"[PASSWORD RESET ERROR] {e}")
            flash("❌ There was an issue sending the reset email. Please try again.", "danger")

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/forgot_password.html",
        title="Forgot Password | PittState-Connect",
        current_year=datetime.now().year,
    )


# ---------------------------------------------------------------------
# 🔐 Reset Password Route
# ---------------------------------------------------------------------
@password_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Verifies token and updates user's password.
    """
    serializer = get_serializer()

    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except SignatureExpired:
        flash("⚠️ This password reset link has expired. Please request a new one.", "warning")
        return redirect(url_for("password.forgot_password"))
    except BadSignature:
        flash("❌ Invalid or tampered link.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("❌ No account found for this email.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "warning")
            return redirect(url_for("password.reset_password", token=token))

        user.password_hash = generate_password_hash(password)
        db.session.commit()

        flash("✅ Your password has been updated successfully!", "success")
        current_app.logger.info(f"[PASSWORD RESET SUCCESS] {user.email}")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html",
        token=token,
        title="Reset Password | PittState-Connect",
        current_year=datetime.now().year,
    )
