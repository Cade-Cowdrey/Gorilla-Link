import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email (SendGrid or SMTP—stubs OK)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "apikey")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "SG.xxxxx")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@pittstate-connect.app")

    # Feature flags
    ENABLE_AI = os.environ.get("ENABLE_AI", "0") == "1"   # safe off by default
    ENABLE_ANALYTICS = True
    ENABLE_SPONSORSHIPS = True
