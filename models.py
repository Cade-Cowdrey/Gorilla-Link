import os
import secrets
import datetime as dt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.orm import relationship
from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy
import pyotp
from loguru import logger

# -----------------------------------------------------------
# Initialize SQLAlchemy (lazy-init)
# -----------------------------------------------------------
db = SQLAlchemy()

# -----------------------------------------------------------
# Constants
# -----------------------------------------------------------
DEFAULT_PROFILE_IMG = "/static/img/defaults/profile_default.png"
DEFAULT_BANNER_IMG = "/static/img/defaults/banner_default.jpg"


# -----------------------------------------------------------
# User and Auth Models
# -----------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    psu_id = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), default="student")  # student, alumni, admin, employer, faculty
    full_name = db.Column(db.String(120))
    major = db.Column(db.String(120))
    graduation_year = db.Column(db.Integer)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    # Profile / settings
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255), default=DEFAULT_PROFILE_IMG)
    banner_url = db.Column(db.String(255), default=DEFAULT_BANNER_IMG)
    is_active_account = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)

    # 2FA fields
    otp_secret = db.Column(db.String(32), nullable=True)

    # Relationships
    posts = relationship("Post", backref="author", lazy=True)
    messages_sent = relationship("Message", backref="sender", lazy=True, foreign_keys="Message.sender_id")
    messages_received = relationship("Message", backref="receiver", lazy=True, foreign_keys="Message.receiver_id")
    tokens = relationship("UserToken", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

    # ---------------------- Password ------------------------
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        db.session.commit()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ---------------------- 2FA ------------------------------
    def enable_2fa(self):
        self.otp_secret = pyotp.random_base32()
        db.session.commit()
        return self.otp_secret

    def get_otp_uri(self):
        return f"otpauth://totp/PittStateConnect:{self.email}?secret={self.otp_secret}&issuer=PittStateConnect"

    def verify_otp(self, token):
        if not self.otp_secret:
            return False
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(token)

    # ---------------------- Token ----------------------------
    def generate_token(self, expires_sec=3600):
        s = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "psu_secret_key"))
        token = s.dumps({"user_id": self.id})
        db.session.add(UserToken(token=token, user_id=self.id, expires_at=dt.datetime.utcnow() + dt.timedelta(seconds=expires_sec)))
        db.session.commit()
        return token

    @staticmethod
    def verify_token(token):
        s = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "psu_secret_key"))
        try:
            data = s.loads(token, max_age=3600)
            return User.query.get(data["user_id"])
        except (BadSignature, SignatureExpired):
            return None

    # ---------------------- Roles ----------------------------
    def has_role(self, *roles):
        return self.role in roles

    def is_admin(self):
        return self.role == "admin"


class UserToken(db.Model):
    __tablename__ = "user_tokens"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    token = db.Column(db.String(512), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    @staticmethod
    def verify_token(token):
        token_obj = UserToken.query.filter_by(token=token).first()
        if token_obj and token_obj.expires_at > dt.datetime.utcnow():
            return token_obj
        return None


# -----------------------------------------------------------
# Academic / Departmental Models
# -----------------------------------------------------------
class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    chair = db.Column(db.String(120))
    email = db.Column(db.String(120))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    users = relationship("User", backref="department", lazy=True)
    scholarships = relationship("Scholarship", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# -----------------------------------------------------------
# Communication Models
# -----------------------------------------------------------
class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=dt.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def mark_read(self):
        self.is_read = True
        db.session.commit()


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(120))
    message = db.Column(db.Text)
    link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def mark_read(self):
        self.is_read = True
        db.session.commit()


# -----------------------------------------------------------
# Scholarship Models
# -----------------------------------------------------------
class Scholarship(db.Model):
    __tablename__ = "scholarships"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    deadline = db.Column(db.DateTime)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    # Optional Phase 2 Enhancements
    criteria = db.Column(db.Text)
    tags = db.Column(db.String(255))
    ai_score = db.Column(db.Float, default=0.0)
    view_count = db.Column(db.Integer, default=0)
    applications = relationship("ScholarshipApplication", backref="scholarship", lazy=True)

    def increment_views(self):
        self.view_count += 1
        db.session.commit()


class ScholarshipApplication(db.Model):
    __tablename__ = "scholarship_applications"
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    essay = db.Column(db.Text)
    status = db.Column(db.String(50), default="Pending")  # Pending, Approved, Rejected
    submitted_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewer_comments = db.Column(db.Text)
    ai_feedback = db.Column(db.Text)

    def approve(self, reviewer_comments=None):
        self.status = "Approved"
        self.reviewed_at = dt.datetime.utcnow()
        self.reviewer_comments = reviewer_comments
        db.session.commit()

    def reject(self, reviewer_comments=None):
        self.status = "Rejected"
        self.reviewed_at = dt.datetime.utcnow()
        self.reviewer_comments = reviewer_comments
        db.session.commit()


# -----------------------------------------------------------
# Posts and Events
# -----------------------------------------------------------
class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    tags = db.Column(db.String(255))

    def like(self):
        self.likes += 1
        db.session.commit()


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    date = db.Column(db.DateTime)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)


# -----------------------------------------------------------
# Analytics and System Logs
# -----------------------------------------------------------
class SystemLog(db.Model):
    __tablename__ = "system_logs"
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(120))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=dt.datetime.utcnow)


class UsageMetric(db.Model):
    __tablename__ = "usage_metrics"
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(120))
    metric_value = db.Column(db.Float)
    collected_at = db.Column(db.DateTime, default=dt.datetime.utcnow)


# -----------------------------------------------------------
# Auto Logging Hooks
# -----------------------------------------------------------
@event.listens_for(User, "after_insert")
def log_user_create(mapper, connection, target):
    connection.execute(
        SystemLog.__table__.insert().values(
            event_type="USER_CREATE",
            description=f"User created: {target.username}",
            user_id=target.id,
            timestamp=dt.datetime.utcnow()
        )
    )


@event.listens_for(ScholarshipApplication, "after_insert")
def log_scholarship_application(mapper, connection, target):
    connection.execute(
        SystemLog.__table__.insert().values(
            event_type="SCHOLARSHIP_APPLY",
            description=f"User {target.user_id} applied for scholarship {target.scholarship_id}",
            timestamp=dt.datetime.utcnow()
        )
    )


# -----------------------------------------------------------
# Database Initializer for Factory Pattern
# -----------------------------------------------------------
def init_models(app):
    """Attach SQLAlchemy to the Flask app context."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        logger.info("✅ Database tables ensured.")
