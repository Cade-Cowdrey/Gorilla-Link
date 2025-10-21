from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# ------------------------------
# Core Models
# ------------------------------

class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    verified = db.Column(db.Boolean, default=False)

    role = db.relationship("Role", backref="users", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def __repr__(self):
        return f"<User {self.email}>"


# ------------------------------
# Scholarship Hub
# ------------------------------

class Scholarship(db.Model):
    __tablename__ = "scholarship"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    deadline = db.Column(db.Date)
    department = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    applications = db.relationship("ScholarshipApplication", backref="scholarship", lazy=True)


class ScholarshipApplication(db.Model):
    __tablename__ = "scholarship_application"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"))
    status = db.Column(db.String(32), default="draft")
    progress = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="scholarship_applications")


class Essay(db.Model):
    __tablename__ = "essay"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="essays")


class Reminder(db.Model):
    __tablename__ = "reminder"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    scholarship_id = db.Column(db.Integer, nullable=True)
    due_at = db.Column(db.DateTime)
    note = db.Column(db.String(255))
    user = db.relationship("User", backref="reminders")


class FinancialLiteracyResource(db.Model):
    __tablename__ = "financial_literacy_resource"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    url = db.Column(db.String(300))
    category = db.Column(db.String(100))


class CostToCompletion(db.Model):
    __tablename__ = "cost_to_completion"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    estimated_tuition_remaining = db.Column(db.Integer, default=0)
    est_graduation_date = db.Column(db.Date)
    user = db.relationship("User", backref="cost_to_completion")


class FundingJourney(db.Model):
    __tablename__ = "funding_journey"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    step = db.Column(db.String(120))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="funding_journey")


class FacultyRecommendation(db.Model):
    __tablename__ = "faculty_recommendation"
    id = db.Column(db.Integer, primary_key=True)
    applicant_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    faculty_name = db.Column(db.String(200))
    file_url = db.Column(db.String(400))
    applicant = db.relationship("User", backref="faculty_recommendations")


class LeaderboardEntry(db.Model):
    __tablename__ = "leaderboard_entry"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    points = db.Column(db.Integer, default=0)
    user = db.relationship("User", backref="leaderboard_entries")


class PeerMentor(db.Model):
    __tablename__ = "peer_mentor"
    id = db.Column(db.Integer, primary_key=True)
    mentor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    mentee_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    mentor = db.relationship("User", foreign_keys=[mentor_user_id], backref="mentees")
    mentee = db.relationship("User", foreign_keys=[mentee_user_id], backref="mentors")


# ------------------------------
# Donors & Impact
# ------------------------------

class Donor(db.Model):
    __tablename__ = "donor"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    organization = db.Column(db.String(200))
    contact_email = db.Column(db.String(200))
    donations = db.relationship("Donation", backref="donor", lazy=True)


class Donation(db.Model):
    __tablename__ = "donation"
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("donor.id"))
    amount = db.Column(db.Integer)
    note = db.Column(db.String(255))
    donated_at = db.Column(db.DateTime, default=datetime.utcnow)


class ImpactStory(db.Model):
    __tablename__ = "impact_story"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    photo_url = db.Column(db.String(400))
    published_at = db.Column(db.DateTime, default=datetime.utcnow)


# ------------------------------
# Admin Activity Log
# ------------------------------

class ActivityLog(db.Model):
    __tablename__ = "activity_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.action} by {self.user_id}>"


# ------------------------------
# Exports
# ------------------------------

__all__ = [
    "db", "User", "Role",
    "Scholarship", "ScholarshipApplication", "Essay", "Reminder",
    "FinancialLiteracyResource", "CostToCompletion", "FundingJourney",
    "FacultyRecommendation", "LeaderboardEntry", "PeerMentor",
    "Donor", "Donation", "ImpactStory", "ActivityLog"
]
