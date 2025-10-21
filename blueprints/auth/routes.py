from flask import Blueprint, render_template
bp = Blueprint("auth_bp", __name__, url_prefix="/auth")

@bp.get("/login")
def login():
    return render_template("auth/login.html")

@bp.get("/register")
def register():
    return render_template("auth/register.html")
