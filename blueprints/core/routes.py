from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_mail import Message
from extensions import mail

core = Blueprint("core", __name__)

# 🏠 Home Page
@core.route("/")
def home():
    return render_template("core/home.html")

# ℹ️ About Page
@core.route("/about")
def about():
    return render_template("core/about.html")

# 👥 Team Page
@core.route("/team")
def team():
    return render_template("core/team.html")

# ✉️ Contact Page
@core.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message_body = request.form.get("message")

        if not name or not email or not message_body:
            flash("Please fill out all required fields before submitting.", "warning")
            return redirect(url_for("core.contact"))

        try:
            msg = Message(
                subject=f"[PittState-Connect Contact] {subject}",
                sender=email,
                recipients=["info@pittstate-connect.com"],
                body=f"From: {name}\nEmail: {email}\n\nMessage:\n{message_body}",
            )
            mail.send(msg)
            flash("✅ Your message has been sent successfully!", "success")
        except Exception as e:
            flash("⚠️ There was an issue sending your message. Please try again later.", "danger")
            print(f"Mail error: {e}")

        return redirect(url_for("core.contact"))

    return render_template("core/contact.html")
