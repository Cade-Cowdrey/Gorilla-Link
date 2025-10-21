import os

def init_mail(app, mail):
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "apikey")
    app.config["MAIL_PASSWORD"] = os.getenv("SENDGRID_API_KEY", "")
    mail.init_app(app)
