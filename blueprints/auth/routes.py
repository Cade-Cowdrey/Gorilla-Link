from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import User
from extensions import db
from utils.analytics_util import record_page_view

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET", "POST"])
def login():
    record_page_view("auth_login")
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("core.home"))
        flash("Invalid credentials.", "danger")
    return render_template("auth/login.html", title="Login | PittState-Connect")

@bp.route("/logout")
@login_required
de
f logout():
    
logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("auth.login"))
