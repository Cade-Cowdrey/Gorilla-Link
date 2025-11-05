"""
Innovative features that PSU doesn't have but desperately needs
These features solve real student problems and create tremendous value
"""

from extensions import db
from datetime import datetime
from sqlalchemy import Index

# ==================== STUDY GROUP FINDER ====================
class StudyGroup(db.Model):
    __tablename__ = 'study_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Course Information
    course_code = db.Column(db.String(20), nullable=False, index=True)
    course_name = db.Column(db.String(200), nullable=False)
    professor_name = db.Column(db.String(200))
    
    # Group Details
    group_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    focus_topics = db.Column(db.Text)  # "Exam prep, homework help, project collaboration"
    
    # Meeting Info
    meeting_location = db.Column(db.String(200))  # "Axe Library Room 201"
    is_virtual = db.Column(db.Boolean, default=False)
    virtual_link = db.Column(db.String(500))
    
    # Schedule
    meeting_schedule = db.Column(db.String(200))  # "Tuesdays 6-8pm, Thursdays 7-9pm"
    next_meeting = db.Column(db.DateTime)
    
    # Capacity
    max_members = db.Column(db.Integer, default=8)
    current_members = db.Column(db.Integer, default=1)
    is_full = db.Column(db.Boolean, default=False)
    
    # Requirements
    gpa_requirement = db.Column(db.Numeric(3, 2))  # Minimum GPA to join
    requires_approval = db.Column(db.Boolean, default=False)
    commitment_level = db.Column(db.String(20))  # casual, moderate, serious
    
    # Group Type
    group_type = db.Column(db.String(50), default='open')  # open, invite_only, exam_prep, project_team
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='study_groups_created')
    
    __table_args__ = (
        Index('idx_study_course_active', 'course_code', 'is_active'),
    )


class StudyGroupMember(db.Model):
    __tablename__ = 'study_group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(20), default='active')  # active, inactive, banned
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_count = db.Column(db.Integer, default=0)
    
    group = db.relationship('StudyGroup', backref='members')
    user = db.relationship('User', backref='study_group_memberships')


# ==================== MENTAL HEALTH & WELLNESS TRACKER ====================
class WellnessCheckIn(db.Model):
    __tablename__ = 'wellness_checkins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Check-in Date
    checkin_date = db.Column(db.Date, nullable=False, index=True)
    
    # Mood Tracking (1-10 scale)
    mood_rating = db.Column(db.Integer)  # 1=terrible, 10=excellent
    stress_level = db.Column(db.Integer)  # 1=no stress, 10=extreme stress
    energy_level = db.Column(db.Integer)
    sleep_quality = db.Column(db.Integer)
    
    # Sleep Tracking
    hours_slept = db.Column(db.Numeric(4, 1))
    
    # Academic Stress Factors
    exam_stress = db.Column(db.Boolean, default=False)
    assignment_stress = db.Column(db.Boolean, default=False)
    financial_stress = db.Column(db.Boolean, default=False)
    social_stress = db.Column(db.Boolean, default=False)
    
    # Self-Care Activities
    exercised_today = db.Column(db.Boolean, default=False)
    ate_healthy = db.Column(db.Boolean, default=False)
    socialized = db.Column(db.Boolean, default=False)
    practiced_selfcare = db.Column(db.Boolean, default=False)
    
    # Notes
    notes = db.Column(db.Text)
    
    # Resources Needed
    needs_counseling = db.Column(db.Boolean, default=False)
    needs_academic_help = db.Column(db.Boolean, default=False)
    needs_financial_help = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='wellness_checkins')


class WellnessResource(db.Model):
    __tablename__ = 'wellness_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Resource Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)  # counseling, crisis, academic, financial, health
    
    # Contact
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(150))
    website = db.Column(db.String(500))
    location = db.Column(db.String(200))
    
    # Availability
    hours = db.Column(db.String(200))
    is_24_7 = db.Column(db.Boolean, default=False)
    is_emergency = db.Column(db.Boolean, default=False)
    
    # Visibility
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)  # Higher number = show first


# ==================== LOST & FOUND ====================
class LostItem(db.Model):
    __tablename__ = 'lost_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Item Type
    item_type = db.Column(db.String(20), nullable=False)  # lost or found
    category = db.Column(db.String(50), nullable=False)  # phone, keys, wallet, laptop, clothing, etc.
    
    # Description
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    brand = db.Column(db.String(100))
    color = db.Column(db.String(50))
    
    # Location & Time
    location = db.Column(db.String(200), nullable=False)  # Where lost/found
    date_lost_found = db.Column(db.Date, nullable=False, index=True)
    time_approximate = db.Column(db.String(50))
    
    # Images
    image_url = db.Column(db.String(500))
    
    # Contact (only for found items)
    contact_method = db.Column(db.String(20))  # email, phone, message
    contact_info = db.Column(db.String(200))  # Encrypted/hashed
    
    # Status
    status = db.Column(db.String(20), default='active', index=True)  # active, claimed, expired
    claimed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Auto-expire after 60 days
    
    user = db.relationship('User', backref='lost_items')
    
    __table_args__ = (
        Index('idx_lost_category_status', 'category', 'status'),
        Index('idx_lost_type_date', 'item_type', 'date_lost_found'),
    )


# ==================== SUBLEASE MARKETPLACE ====================
class SubleasePosting(db.Model):
    __tablename__ = 'sublease_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Property Details
    title = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    property_type = db.Column(db.String(50))  # apartment, house, room
    
    # Lease Terms
    available_from = db.Column(db.Date, nullable=False, index=True)
    available_until = db.Column(db.Date, nullable=False)
    monthly_rent = db.Column(db.Numeric(10, 2), nullable=False)
    security_deposit = db.Column(db.Numeric(10, 2))
    
    # Space Details
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Numeric(3, 1))
    square_feet = db.Column(db.Integer)
    furnished = db.Column(db.Boolean, default=False)
    
    # Utilities
    utilities_included = db.Column(db.Text)  # "Water, Trash, Internet"
    estimated_utilities = db.Column(db.Numeric(8, 2))
    
    # Roommates
    has_roommates = db.Column(db.Boolean, default=False)
    number_of_roommates = db.Column(db.Integer)
    roommate_gender_preference = db.Column(db.String(20))
    
    # Features
    parking_available = db.Column(db.Boolean, default=False)
    pets_allowed = db.Column(db.Boolean, default=False)
    laundry = db.Column(db.String(50))  # in_unit, on_site, none
    
    # Description
    description = db.Column(db.Text, nullable=False)
    reason_for_sublease = db.Column(db.Text)
    
    # Images
    image_urls = db.Column(db.Text)  # JSON array of image URLs
    
    # Contact
    contact_preference = db.Column(db.String(20), default='message')
    phone_visible = db.Column(db.Boolean, default=False)
    
    # Requirements
    credit_check_required = db.Column(db.Boolean, default=False)
    income_verification = db.Column(db.Boolean, default=False)
    
    # Status
    status = db.Column(db.String(20), default='available', index=True)  # available, pending, rented
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    
    user = db.relationship('User', backref='sublease_postings')

# ==================== FREE STUFF / GIVE AWAY ====================
class FreeStuff(db.Model):
    __tablename__ = 'free_stuff'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Item Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)  # furniture, electronics, clothes, books, misc
    condition = db.Column(db.String(50))  # new, like_new, good, fair, poor
    
    # Images
    image_urls = db.Column(db.Text)  # JSON array
    
    # Pickup Details
    pickup_location = db.Column(db.String(200), nullable=False)
    available_until = db.Column(db.Date)
    pickup_instructions = db.Column(db.Text)
    
    # Preferences
    first_come_first_serve = db.Column(db.Boolean, default=True)
    student_only = db.Column(db.Boolean, default=True)
    
    # Status
    status = db.Column(db.String(20), default='available', index=True)  # available, claimed, expired
    claimed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    claimed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    
    giver = db.relationship('User', foreign_keys=[user_id], backref='items_given')
    claimer = db.relationship('User', foreign_keys=[claimed_by_id], backref='items_claimed')
