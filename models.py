# ================================================================
# 🦍 PittState-Connect — Full Database Models
# ================================================================
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# ================================================================
# 🔐 USER MODEL (Authentication)
# ================================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    role = db.Column(db.String(50), default="student")  # student, alumni, admin
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    avatar_url = db.Column(db.String(255))
    headline = db.Column(db.String(200))
    bio = db.Column(db.Text)

    total_posts = db.Column(db.Integer, default=0)
    total_connections = db.Column(db.Integer, default=0)
    total_badges = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts = db.relationship("Post", backref="author", lazy=True)
    messages_sent = db.relationship("Message", foreign_keys="Message.sender_id", backref="sender", lazy=True)
    messages_received = db.relationship("Message", foreign_keys="Message.receiver_id", backref="receiver", lazy=True)
    events = db.relationship("Event", backref="creator", lazy=True)
    notifications = db.relationship("Notification", backref="recipient", lazy=True)
    badges = db.relationship("UserBadge", backref="user", lazy=True)
    connections = db.relationship("Connection", foreign_keys="Connection.user_id", backref="user", lazy=True)

    # 🔐 Security helpers
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.id}: {self.name} ({self.role})>"


# ================================================================
# 🎓 DEPARTMENTS
# ================================================================
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    faculty_count = db.Column(db.Integer, default=0)
    student_count = db.Column(db.Integer, default=0)
    alumni_count = db.Column(db.Integer, default=0)

    users = db.relationship("User", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# ================================================================
# 💬 POSTS (Feed / Discussions)
# ================================================================
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    replies = db.relationship("Reply", backref="post", lazy=True)

    def __repr__(self):
        return f"<Post {self.id} by {self.user_id}>"


# ================================================================
# 💬 REPLIES (Nested under Posts)
# ================================================================
class Reply(db.Model):
    __tablename__ = "replies"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Reply {self.id} on Post {self.post_id}>"


# ================================================================
# ✉️ MESSAGES (Direct Messages)
# ================================================================
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} to {self.receiver_id}>"


# ================================================================
# 📅 EVENTS (Campus & Alumni)
# ================================================================
class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return f"<Event {self.title}>"


# ================================================================
# 🔔 NOTIFICATIONS
# ================================================================
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id} for User {self.user_id}>"


# ================================================================
# 💼 JOBS & INTERNSHIPS
# ================================================================
class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150))
    description = db.Column(db.Text)
    link = db.Column(db.String(255))
    location = db.Column(db.String(150))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"


# ================================================================
# 🪙 BADGES (Gamified Achievements)
# ================================================================
class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Badge {self.name}>"


class UserBadge(db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    badge = db.relationship("Badge", backref="user_badges", lazy=True)

    def __repr__(self):
        return f"<UserBadge {self.user_id}-{self.badge_id}>"


# ================================================================
# 🔗 CONNECTIONS (Networking / Mentorship)
# ================================================================
class Connection(db.Model):
    __tablename__ = "connections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    connected_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, accepted, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Connection {self.user_id} ↔ {self.connected_user_id} ({self.status})>"


# ================================================================
# 📰 WEEKLY DIGESTS (Email Campaigns)
# ================================================================
class DigestArchive(db.Model):
    __tablename__ = "digest_archives"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255))
    content_html = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    audience = db.Column(db.String(50), default="students")  # students, alumni, all

    def __repr__(self):
        return f"<DigestArchive {self.subject}>"


class EmailDigestLog(db.Model):
    __tablename__ = "email_digest_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    digest_id = db.Column(db.Integer, db.ForeignKey("digest_archives.id"))
    status = db.Column(db.String(50), default="sent")  # sent, opened, bounced
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="email_logs", lazy=True)
    digest = db.relationship("DigestArchive", backref="email_logs", lazy=True)

    def __repr__(self):
        return f"<EmailDigestLog user={self.user_id} digest={self.digest_id}>"


# ================================================================
# 📊 PLATFORM STATISTICS (Insights)
# ================================================================
class PlatformStat(db.Model):
    __tablename__ = "platform_stats"

    id = db.Column(db.Integer, primary_key=True)
    active_users = db.Column(db.Integer, default=0)
    posts_shared = db.Column(db.Integer, default=0)
    connections_made = db.Column(db.Integer, default=0)
    jobs_posted = db.Column(db.Integer, default=0)
    events_created = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PlatformStat {self.id}>"
