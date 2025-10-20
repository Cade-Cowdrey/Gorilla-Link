# ================================================================
# 🦍 PittState-Connect — Unified Models File
# ================================================================
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# ================================================================
# 👥 Users
# ================================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(50), default="student")  # student, alumni, admin
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship("Post", backref="author", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)
    events = db.relationship("Event", backref="creator", lazy=True)
    badges = db.relationship("UserBadge", backref="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash or "", password)

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"


# ================================================================
# 🏫 Departments
# ================================================================
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# ================================================================
# 💬 Posts / Feed
# ================================================================
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    likes = db.relationship("Like", backref="post", lazy=True)
    replies = db.relationship("Reply", backref="post", lazy=True)

    def __repr__(self):
        return f"<Post {self.id} by {self.author_id}>"


# ================================================================
# ❤️ Likes / Engagement
# ================================================================
class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================================================================
# 💬 Replies
# ================================================================
class Reply(db.Model):
    __tablename__ = "replies"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================================================================
# 📅 Events
# ================================================================
class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Event {self.title}>"


# ================================================================
# 🔔 Notifications
# ================================================================
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================================================================
# 💼 Job / Internship Opportunities
# ================================================================
class JobOpportunity(db.Model):
    __tablename__ = "job_opportunities"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(150))
    description = db.Column(db.Text)
    link = db.Column(db.String(255))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<JobOpportunity {self.title}>"


# ================================================================
# 🧑‍🤝‍🧑 Mentorship
# ================================================================
class Mentorship(db.Model):
    __tablename__ = "mentorships"

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<Mentorship {self.mentor_id}->{self.mentee_id} ({self.status})>"


# ================================================================
# 🧩 Groups (Campus Clubs / Organizations)
# ================================================================
class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Group {self.name}>"


# ================================================================
# 📰 Stories (Alumni / Student Highlights)
# ================================================================
class Story(db.Model):
    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    published_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Story {self.title}>"


# ================================================================
# 🏅 Badges
# ================================================================
class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"))
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================================================================
# 📨 Digest Archives
# ================================================================
class DigestArchive(db.Model):
    __tablename__ = "digest_archives"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content_html = db.Column(db.Text)
    audience = db.Column(db.String(50), default="all")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================================================================
# 🤝 Connections
# ================================================================
class Connection(db.Model):
    __tablename__ = "connections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    connection_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================================================================
# 📈 Analytics
# ================================================================
class SiteStat(db.Model):
    __tablename__ = "site_stats"

    id = db.Column(db.Integer, primary_key=True)
    metric = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Integer, default=0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SiteStat {self.metric}: {self.value}>"
