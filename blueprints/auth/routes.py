from flask import Blueprint, render_template, redirect, url_for, request, flash

auth_bp = Blueprint("auth_bp", __name__, template_folder="../../templates")

@auth_bp.route("/login")
def login():
    return render_template("auth/login.html")

@auth_bp.route("/register")
def register():
    return render_template("auth/register.html")

@auth_bp.route("/forgot")
def forgot():
    return render_template("auth/forgot.html")
