from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db
from utils.analytics_util import record_page_view

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET", "POST"])
def login():
    record_page_view("auth_login")
    if request.method == "POST":
        username = request.form.get("username") or request.form.get("email")
        password = request.form.get("password")
        
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for("core.home"))
        flash("Invalid credentials.", "danger")
    return render_template("auth/login.html", title="Login | PittState-Connect")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))

