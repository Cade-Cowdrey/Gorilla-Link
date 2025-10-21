import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.getenv("REDIS_URL")

    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@pittstate-connect.edu")
    MAIL_SUPPRESS_SEND = False

    # AWS S3
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    # Branding
    PSU_BRAND_PRIMARY = "#991B1E"   # Crimson
    PSU_BRAND_ACCENT  = "#FDB913"   # Gold

    # OpenAI (for essay helper)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
