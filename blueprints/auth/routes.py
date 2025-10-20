from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager
from models import User  # Make sure your models.py defines User properly

auth_bp = Blueprint("auth", __name__, template_folder="templates/auth")

# -----------------------------------------------------------
# 🔐 LOGIN MANAGER CONFIGURATION
# -----------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """Flask-Login: Load a user from the database."""
    return db.session.get(User, int(user_id))


# -----------------------------------------------------------
# 🧍 REGISTER — PSU-Branded Signup Page
# -----------------------------------------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Render or handle registration form for new users."""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate basic input
        if not name or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("auth.register"))

        # Check if email already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("That email is already registered.", "danger")
            return redirect(url_for("auth.register"))

        # Create new user
        new_user = User(
            name=name.strip(),
            email=email.strip().lower(),
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        flash("🎉 Registration successful! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", title="Register | PittState-Connect")


# -----------------------------------------------------------
# 🔑 LOGIN — PSU-Branded Login Page
# -----------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render or handle login form."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email.lower()).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("core.home"))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("auth/login.html", title="Login | PittState-Connect")


# -----------------------------------------------------------
# 🚪 LOGOUT — Ends user session
# -----------------------------------------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    """Log the current user out."""
    logout_user()
    flash("You’ve been logged out successfully.", "info")
    return redirect(url_for("core.home"))
