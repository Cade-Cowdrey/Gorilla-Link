import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from extensions import db

# ---------------------------
# USER & AUTH MODELS
# ---------------------------

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship("User", back_populates="role", lazy=True)

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    major = db.Column(db.String(120))
    graduation_year = db.Column(db.Integer)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    date_joined = db.Column(db.DateTime, default=func.now())
    last_login = db.Column(db.DateTime, default=func.now())

    # Relationships
    role = db.relationship("Role", back_populates="users", lazy=True)
    posts = db.relationship("Post", back_populates="author", lazy=True)
    connections = db.relationship("Connection", back_populates="user", lazy=True)
    notifications = db.relationship("Notification", back_populates="recipient", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email}>"

# ---------------------------
# CONTENT MODELS
# ---------------------------

class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())
    image_url = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    likes = db.Column(db.Integer, default=0)
    visibility = db.Column(db.String(32), default="public")

    author = db.relationship("User", back_populates="posts", lazy=True)

    def __repr__(self):
        return f"<Post {self.id} by {self.author_id}>"


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    chair_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    scholarships = db.relationship("Scholarship", back_populates="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.String(255))
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))

    def __repr__(self):
        return f"<Event {self.title}>"

# ---------------------------
# NETWORK & COMMUNICATION
# ---------------------------

class Connection(db.Model):
    __tablename__ = "connections"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    connected_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=func.now())

    user = db.relationship("User", foreign_keys=[user_id], back_populates="connections")

    def __repr__(self):
        return f"<Connection {self.user_id} → {self.connected_user_id} ({self.status})>"


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(64), default="info")
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=func.now())

    recipient = db.relationship("User", back_populates="notifications", lazy=True)

    def __repr__(self):
        return f"<Notification to {self.recipient_id}: {self.message[:20]}>"

# ---------------------------
# SCHOLARSHIP & CAREER MODELS
# ---------------------------

class Scholarship(db.Model):
    __tablename__ = "scholarships"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)
    deadline = db.Column(db.Date)
    eligibility = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime, default=func.now())

    department = db.relationship("Department", back_populates="scholarships", lazy=True)

    def __repr__(self):
        return f"<Scholarship {self.title}>"

class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    posted_at = db.Column(db.DateTime, default=func.now())
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"

# ---------------------------
# ANALYTICS & TRACKING
# ---------------------------

class PageView(db.Model):
    __tablename__ = "page_views"
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=func.now())
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    def __repr__(self):
        return f"<PageView {self.page_name} by {self.user_id or 'Guest'}>"


class AnalyticsSummary(db.Model):
    __tablename__ = "analytics_summary"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.date.today)
    page_views = db.Column(db.Integer, default=0)
    active_users = db.Column(db.Integer, default=0)
    new_users = db.Column(db.Integer, default=0)
    scholarships_viewed = db.Column(db.Integer, default=0)
    jobs_viewed = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<AnalyticsSummary {self.date}>"

class ApiUsage(db.Model):
    __tablename__ = "api_usage"
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=func.now())
    response_time_ms = db.Column(db.Float)
    status_code = db.Column(db.Integer)
    tokens_used = db.Column(db.Integer, default=0)  # for AI/OpenAI tracking
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))

    def __repr__(self):
        return f"<ApiUsage {self.endpoint} ({self.status_code})>"

# ---------------------------
# HELPER METHODS
# ---------------------------

def track_page_view(page_name, user_id=None, ip_address=None, user_agent=None):
    """Log page views for analytics tracking."""
    view = PageView(
        page_name=page_name,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(view)
    db.session.commit()
