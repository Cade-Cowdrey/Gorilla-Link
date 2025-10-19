from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app_pro import db


# ==========================================================
# 🧍 USER MODEL (Flask-Login compatible)
# ==========================================================
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="student")  # student, alumni, admin
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    posts = db.relationship("Post", backref="author", lazy=True)
    messages_sent = db.relationship(
        "Message",
        foreign_keys="Message.sender_id",
        backref="sender",
        lazy=True,
        cascade="all, delete-orphan",
    )
    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        backref="receiver",
        lazy=True,
        cascade="all, delete-orphan",
    )
    notifications = db.relationship("Notification", backref="user", lazy=True)
    jobs_posted = db.relationship("Job", backref="poster", lazy=True)
    events_created = db.relationship("Event", backref="creator", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email}>"


# ==========================================================
# 🎓 DEPARTMENT MODEL
# ==========================================================
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    faculty_head = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# ==========================================================
# 📰 POST MODEL
# ==========================================================
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150))
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)

    likes = db.relationship("Like", backref="post", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("Reply", backref="post", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post {self.id} by User {self.user_id}>"


# ==========================================================
# 💬 MESSAGE MODEL
# ==========================================================
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} to {self.receiver_id}>"


# ==========================================================
# 🔔 NOTIFICATION MODEL
# ==========================================================
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255))
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id}>"


# ==========================================================
# ❤️ LIKE MODEL
# ==========================================================
class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Like user={self.user_id} post={self.post_id}>"


# ==========================================================
# 💬 REPLY MODEL
# ==========================================================
class Reply(db.Model):
    __tablename__ = "replies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Reply {self.id}>"


# ==========================================================
# 🏅 BADGE MODEL
# ==========================================================
class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Badge {self.name}>"


# ==========================================================
# 🧩 CONNECTION MODEL
# ==========================================================
class Connection(db.Model):
    __tablename__ = "connections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    connected_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(20), default="pending")  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Connection {self.user_id} ↔ {self.connected_user_id} ({self.status})>"


# ==========================================================
# 💼 JOB / INTERNSHIP MODEL
# ==========================================================
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(120))
    location = db.Column(db.String(120))
    job_type = db.Column(db.String(50))  # Full-time, Internship, Part-time
    description = db.Column(db.Text)
    posted_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"


# ==========================================================
# 🎟️ EVENT MODEL
# ==========================================================
class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(150))
    event_date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Event {self.title} on {self.event_date}>"


# ==========================================================
# 🗞️ DIGEST ARCHIVE MODEL
# ==========================================================
class DigestArchive(db.Model):
    __tablename__ = "digest_archives"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    summary = db.Column(db.Text)
    pdf_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DigestArchive {self.title}>"


# ==========================================================
# ✉️ EMAIL DIGEST LOG MODEL
# ==========================================================
class EmailDigestLog(db.Model):
    __tablename__ = "email_digest_logs"

    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(120))
    subject = db.Column(db.String(255))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="sent")

    def __repr__(self):
        return f"<EmailDigestLog {self.recipient_email}>"
