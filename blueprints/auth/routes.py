from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required

from extensions import db
from models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("core.home"))
        flash("Invalid email or password.", "warn")
    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("core.home"))
    if request.method == "POST":
        first = request.form.get("first_name").strip()
        last = request.form.get("last_name").strip()
        email = request.form.get("email", "").lower().strip()
        pw = request.form.get("password")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warn")
            return redirect(url_for("auth.register"))
        user = User(first_name=first, last_name=last, email=email)
        user.set_password(pw)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("core.home"))
