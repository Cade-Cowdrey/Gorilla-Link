from datetime import datetime
from extensions import db
from flask_login import UserMixin

# -------------------------------------------------
# 🧠 USER MODEL
# -------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default="student")  # student, alumni, faculty, staff, admin
    bio = db.Column(db.Text)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    graduation_year = db.Column(db.String(10))
    profile_image = db.Column(db.String(200))
    visibility = db.Column(db.String(50), default="public")
    notifications_enabled = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts = db.relationship("Post", backref="author", lazy=True)
    badges = db.relationship("Badge", backref="user", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)
    events_attending = db.relationship(
        "Event",
        secondary="event_attendees",
        back_populates="attendees"
    )

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"


# -------------------------------------------------
# 🏛️ DEPARTMENT MODEL
# -------------------------------------------------
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    head = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship("User", backref="department", lazy=True)
    posts = db.relationship("Post", backref="department", lazy=True)
    events = db.relationship("Event", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# -------------------------------------------------
# 📰 POST MODEL
# -------------------------------------------------
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="general")  # general, career, announcement
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    location = db.Column(db.String(120))
    link = db.Column(db.String(300))
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Post {self.title or self.content[:20]} by {self.user_id}>"


# -------------------------------------------------
# 🎟️ EVENT MODEL
# -------------------------------------------------
class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    attendees = db.relationship(
        "User",
        secondary="event_attendees",
        back_populates="events_attending"
    )

    def __repr__(self):
        return f"<Event {self.title}>"


# -------------------------------------------------
# 🔔 NOTIFICATION MODEL
# -------------------------------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150))
    message = db.Column(db.Text)
    link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.title} to User {self.user_id}>"


# -------------------------------------------------
# 🏅 BADGE MODEL
# -------------------------------------------------
class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Badge {self.title} for User {self.user_id}>"


# -------------------------------------------------
# 🤝 EVENT ATTENDEE ASSOCIATION TABLE
# -------------------------------------------------
event_attendees = db.Table(
    "event_attendees",
    db.Column("event_id", db.Integer, db.ForeignKey("events.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)
