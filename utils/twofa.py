# utils/twofa.py
import pyotp
from flask import current_app

def get_totp_for(user_email: str) -> pyotp.TOTP:
    secret = (current_app.config.get("TOTP_SECRET_BASE") or "PSU_DEV_SECRET") + user_email
    return pyotp.TOTP(pyotp.random_base32() if current_app.config.get("TOTP_PER_USER_RANDOM") else pyotp.random_base32(16))

def is_valid(code: str, user_email: str) -> bool:
    # In production, store per-user secret; demo uses a volatile totp.
    totp = get_totp_for(user_email)
    return totp.verify(code, valid_window=1)
