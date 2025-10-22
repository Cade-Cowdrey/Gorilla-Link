# ============================================================
# FILE: blueprints/auth/routes.py
# ============================================================
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from . import auth_bp

# Safe placeholders; wire to real models later
class _UserStub:
    def __init__(self, email):
        self.id = 1
        self.email = email
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    def get_id(self): return "1"

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        # TODO: lookup real user; verify password
        user = _UserStub(email)
        login_user(user)
        flash("Welcome back!", "success")
        return redirect(url_for("core_bp.home"))
    return render_template("auth/login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out successfully.", "info")
    return redirect(url_for("auth_bp.login"))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # TODO: create real user record
        _ = generate_password_hash(request.form.get("password", ""))
        flash("Account created. Please sign in.", "success")
        return redirect(url_for("auth_bp.login"))
    return render_template("auth/register.html")
