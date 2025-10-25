# utils/twofa.py
import pyotp
from flask import current_app

def get_totp_for(user_email: str) -> pyotp.TOTP:
    # In production, store per-user immutable secret; this is a demo helper.
    base = current_app.config.get("TOTP_SECRET_BASE", "PSU_DEV_SECRET")
    # For a real system, retrieve user's stored secret instead of generating each time.
    secret = pyotp.random_base32()
    return pyotp.TOTP(secret)

def is_valid(code: str, user_email: str) -> bool:
    totp = get_totp_for(user_email)
    return totp.verify(code, valid_window=1)
