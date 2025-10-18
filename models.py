# ==========================================================
#  PSU • PittState-Connect  |  Gorilla-Link
#  Unified Models — Final Production Version
# ==========================================================
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship

db = SQLAlchemy()


# ==========================================================
#  Mixins
# ==========================================================
class TimestampMixin:
    """Adds created_at / updated_at timestamps."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==========================================================
#  Core Roles & Users
# ==========================================================
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))

    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_image = db.Column(db.String(255))
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    # relationships
    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    posts = relationship("Post", back_populates="author", lazy="dynamic")
    connections = relationship("Connection", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("UserAnalytics", back_populates="user", uselist=False)
    alumni_profile = relationship("Alumni", back_populates="user", uselist=False)

    def __repr__(self):
        return f"<User {self.email}>"


# ==========================================================
#  Departments, Careers, Companies, Alumni, Events
# ==========================================================
class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)

    users = relationship("User", back_populates="department")
    events = relationship("Event", back_populates="department")
    jobs = relationship("JobInternship", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


class Company(TimestampMixin, db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    industry = db.Column(db.String(150))
    location = db.Column(db.String(150))
    description = db.Column(db.Text)
    website = db.Column(db.String(255))

    jobs = relationship("JobInternship", back_populates="company")

    def __repr__(self):
        return f"<Company {self.name}>"


class JobInternship(TimestampMixin, db.Model):
    __tablename__ = "jobs_internships"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    location = db.Column(db.String(150))
    link = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))

    department = relationship("Department", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")

    def __repr__(self):
        return f"<JobInternship {self.title}>"


class Alumni(TimestampMixin, db.Model):
    __tablename__ = "alumni"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    graduation_year = db.Column(db.Integer)
    company = db.Column(db.String(255))
    position = db.Column(db.String(255))

    user = relationship("User", back_populates="alumni_profile")

    def __repr__(self):
        return f"<Alumni {self.user.email if self.user else self.id}>"


class Event(TimestampMixin, db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    description = db.Column(db.Text)
    location = db.Column(db.String(150))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))

    department = relationship("Department", back_populates="events")

    def __repr__(self):
        return f"<Event {self.title}>"


# ==========================================================
#  Feed, Stories, Engagement, Groups
# ==========================================================
class Post(TimestampMixin, db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    visibility = db.Column(db.String(50), default="public")

    author = relationship("User", back_populates="posts")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post {self.id}>"


class Story(TimestampMixin, db.Model):
    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    image_url = db.Column(db.String(255))

    def __repr__(self):
        return f"<Story {self.title}>"


class Like(TimestampMixin, db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))

    post = relationship("Post", back_populates="likes")

    def __repr__(self):
        return f"<Like user={self.user_id} post={self.post_id}>"


class Comment(TimestampMixin, db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text, nullable=False)

    post = relationship("Post", back_populates="comments")

    def __repr__(self):
        return f"<Comment {self.id}>"


class Group(TimestampMixin, db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    messages = relationship("GroupMessage", back_populates="group")

    def __repr__(self):
        return f"<Group {self.name}>"


class GroupMessage(TimestampMixin, db.Model):
    __tablename__ = "group_messages"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    message = db.Column(db.Text)

    group = relationship("Group", back_populates="messages")

    def __repr__(self):
        return f"<GroupMessage {self.id}>"


# ==========================================================
#  Mentorship & Connections
# ==========================================================
class Mentorship(TimestampMixin, db.Model):
    __tablename__ = "mentorships"

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    mentee_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(50), default="pending")

    def __repr__(self):
        return f"<Mentorship mentor={self.mentor_id} mentee={self.mentee_id}>"


class Connection(TimestampMixin, db.Model):
    __tablename__ = "connections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    connected_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(50), default="pending")

    user = relationship("User", foreign_keys=[user_id], back_populates="connections")

    def __repr__(self):
        return f"<Connection {self.user_id}->{self.connected_user_id}>"


# ==========================================================
#  Notifications, Badges, Analytics
# ==========================================================
class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Notification {self.id}>"


class CareerBadge(TimestampMixin, db.Model):
    __tablename__ = "career_badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.Text)
    icon = db.Column(db.String(255))

    def __repr__(self):
        return f"<CareerBadge {self.name}>"


class UserBadge(TimestampMixin, db.Model):
    __tablename__ = "user_badges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    badge_id = db.Column(db.Integer, db.ForeignKey("career_badges.id"))
    awarded_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserBadge user={self.user_id} badge={self.badge_id}>"


class UserAnalytics(TimestampMixin, db.Model):
    """Tracks user engagement, activity, and network growth."""
    __tablename__ = "user_analytics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    profile_views = db.Column(db.Integer, default=0)
    post_views = db.Column(db.Integer, default=0)
    connections_made = db.Column(db.Integer, default=0)
    messages_sent = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analytics")

    def __repr__(self):
        return f"<UserAnalytics user={self.user_id}>"
