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


@bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    record_page_view("auth_register")
    
    if current_user.is_authenticated:
        return redirect(url_for("core.home"))
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html", title="Register | PittState-Connect")
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html", title="Register | PittState-Connect")
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("auth/register.html", title="Register | PittState-Connect")
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register.html", title="Register | PittState-Connect")
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/register.html", title="Register | PittState-Connect")

