from extensions import db

# Core example table (non-invasive)
class ExampleModel(db.Model):
    __tablename__ = "example_model"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

# Scholarships ecosystem (add-on)
class Scholarship(db.Model):
    __tablename__ = "scholarship"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Integer)
    deadline = db.Column(db.Date)
    department = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)

class ScholarshipApplication(db.Model):
    __tablename__ = "scholarship_application"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"))
    status = db.Column(db.String(32), default="draft")  # draft, submitted, awarded, rejected
    progress = db.Column(db.Integer, default=0)  # 0-100
    submitted_at = db.Column(db.DateTime)
    scholarship = db.relationship("Scholarship", backref="applications")

class Essay(db.Model):
    __tablename__ = "essay"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    last_updated = db.Column(db.DateTime)

class Reminder(db.Model):
    __tablename__ = "reminder"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarship.id"), nullable=True)
    due_at = db.Column(db.DateTime)
    note = db.Column(db.String(255))

class FinancialLiteracyResource(db.Model):
    __tablename__ = "financial_literacy_resource"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    url = db.Column(db.String(300))
    category = db.Column(db.String(100))  # budgeting, loans, grants, etc.

class CostToCompletion(db.Model):
    __tablename__ = "cost_to_completion"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    estimated_tuition_remaining = db.Column(db.Integer, default=0)
    est_graduation_date = db.Column(db.Date)

class FundingJourney(db.Model):
    __tablename__ = "funding_journey"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    step = db.Column(db.String(120))  # FAFSA, dept scholarships, donor awards, etc.
    timestamp = db.Column(db.DateTime)

class FacultyRecommendation(db.Model):
    __tablename__ = "faculty_recommendation"
    id = db.Column(db.Integer, primary_key=True)
    applicant_user_id = db.Column(db.Integer, index=True)
    faculty_name = db.Column(db.String(200))
    file_url = db.Column(db.String(400))

class LeaderboardEntry(db.Model):
    __tablename__ = "leaderboard_entry"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    points = db.Column(db.Integer, default=0)  # opt-in Gorilla Scholars leaderboard

class PeerMentor(db.Model):
    __tablename__ = "peer_mentor"
    id = db.Column(db.Integer, primary_key=True)
    mentor_user_id = db.Column(db.Integer, index=True)
    mentee_user_id = db.Column(db.Integer, index=True)

class Donor(db.Model):
    __tablename__ = "donor"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    organization = db.Column(db.String(200))
    contact_email = db.Column(db.String(200))

class Donation(db.Model):
    __tablename__ = "donation"
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("donor.id"))
    amount = db.Column(db.Integer)
    note = db.Column(db.String(255))
    donor = db.relationship("Donor", backref="donations")

class ImpactStory(db.Model):
    __tablename__ = "impact_story"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    photo_url = db.Column(db.String(400))
    published_at = db.Column(db.DateTime)
