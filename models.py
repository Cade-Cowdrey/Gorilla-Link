# ---------------------------------------------------------
# 🦍 PittState-Connect / Gorilla-Link
# Full Database Models (Flask SQLAlchemy)
# ---------------------------------------------------------
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# ---------------------------------------------------------
# 🧍 USER MODEL
# ---------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="student")
    is_verified = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(255))
    bio = db.Column(db.Text)
    major = db.Column(db.String(120))
    graduation_year = db.Column(db.Integer)
    linkedin_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relationships
    posts = db.relationship("Post", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    notifications = db.relationship("Notification", backref="recipient", lazy=True)
    audit_logs = db.relationship("AuditLog", backref="user", lazy=True)
    events = db.relationship("Event", backref="organizer", lazy=True)
    badges = db.relationship("Badge", backref="awarded_to", lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.id} | {self.email}>"


# ---------------------------------------------------------
# 🏫 DEPARTMENT MODEL
# ---------------------------------------------------------
class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text)
    faculty_head = db.Column(db.String(120))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=db.func.now())

    posts = db.relationship("Post", backref="department", lazy=True)
    events = db.relationship("Event", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


# ---------------------------------------------------------
# 🧵 POST MODEL
# ---------------------------------------------------------
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    comments = db.relationship("Comment", backref="post", lazy=True)

    def __repr__(self):
        return f"<Post {self.id} | {self.title}>"


# ---------------------------------------------------------
# 💬 COMMENT MODEL
# ---------------------------------------------------------
class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"


# ---------------------------------------------------------
# 🎉 EVENT MODEL
# ---------------------------------------------------------
class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(255))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<Event {self.title}>"


# ---------------------------------------------------------
# 🔔 NOTIFICATION MODEL
# ---------------------------------------------------------
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<Notification {self.id} to User {self.user_id}>"


# ---------------------------------------------------------
# 🏅 BADGE MODEL
# ---------------------------------------------------------
class Badge(db.Model):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(255))  # e.g., /static/images/badges/leadership.png
    category = db.Column(db.String(100))  # leadership, academics, service, etc.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    awarded_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<Badge {self.name} for User {self.user_id}>"


# ---------------------------------------------------------
# 🧾 AUDIT LOG MODEL
# ---------------------------------------------------------
class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"<AuditLog {self.id} | {self.action}>"


# ---------------------------------------------------------
# 🧩 SEED HELPERS
# ---------------------------------------------------------
def create_default_admin():
    """Ensure default admin exists."""
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(
            name="PittState Admin",
            email="admin@pittstateconnect.edu",
            role="admin",
            is_verified=True,
        )
        admin.set_password("gorillalink2025")
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin created.")
    else:
        print("ℹ️ Admin already exists.")


def seed_departments():
    """Create default departments for PSU."""
    departments = [
        {"name": "Computer Science", "description": "Programming, AI, and Systems"},
        {"name": "Business Administration", "description": "Finance and Marketing"},
        {"name": "Engineering Technology", "description": "Design and Manufacturing"},
        {"name": "Communication", "description": "Media, PR, and Journalism"},
        {"name": "Education", "description": "Teaching and Leadership"},
    ]
    for d in departments:
        if not Department.query.filter_by(name=d["name"]).first():
            db.session.add(Department(**d))
    db.session.commit()
    print("🏫 Departments seeded.")
