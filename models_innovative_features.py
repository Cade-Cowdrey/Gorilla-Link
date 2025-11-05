"""
Innovative features that PSU doesn't have but desperately needs
These features solve real student problems and create tremendous value
"""

from extensions import db
from datetime import datetime
from sqlalchemy import Index

# ==================== CARPOOL & RIDESHARE BOARD ====================
class RideShare(db.Model):
    __tablename__ = 'ride_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Trip Details
    trip_type = db.Column(db.String(20), nullable=False)  # one_time, recurring
    direction = db.Column(db.String(20), nullable=False)  # to_campus, from_campus, round_trip
    
    # Locations
    origin_city = db.Column(db.String(100), nullable=False)
    origin_state = db.Column(db.String(2))
    origin_zip = db.Column(db.String(10))
    destination_city = db.Column(db.String(100), nullable=False)
    
    # Schedule
    departure_date = db.Column(db.DateTime, nullable=False, index=True)
    departure_time = db.Column(db.String(10))  # "9:00 AM"
    return_date = db.Column(db.DateTime)
    flexible_time = db.Column(db.Boolean, default=False)
    
    # Recurring Details
    recurring_days = db.Column(db.String(50))  # "Monday,Wednesday,Friday"
    recurring_until = db.Column(db.Date)
    
    # Capacity
    available_seats = db.Column(db.Integer, nullable=False)
    total_seats = db.Column(db.Integer)
    
    # Cost
    cost_per_person = db.Column(db.Numeric(6, 2), default=0)  # Gas money split
    is_free = db.Column(db.Boolean, default=True)
    
    # Preferences
    no_smoking = db.Column(db.Boolean, default=True)
    luggage_space = db.Column(db.Boolean, default=True)
    stops_allowed = db.Column(db.Boolean, default=True)
    music_preference = db.Column(db.String(50))
    
    # Details
    notes = db.Column(db.Text)
    phone_number = db.Column(db.String(20))  # For quick contact
    
    # Status
    status = db.Column(db.String(20), default='active', index=True)  # active, full, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    
    # Relationships
    driver = db.relationship('User', foreign_keys=[driver_id], backref='rides_offered')
    
    __table_args__ = (
        Index('idx_ride_date_origin', 'departure_date', 'origin_city'),
        Index('idx_ride_status_date', 'status', 'departure_date'),
    )


class RideRequest(db.Model):
    __tablename__ = 'ride_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride_shares.id'), nullable=False)
    rider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    seats_requested = db.Column(db.Integer, default=1)
    message = db.Column(db.Text)
    
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, cancelled
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    
    # Relationships
    ride = db.relationship('RideShare', backref='requests')
    rider = db.relationship('User', backref='ride_requests')


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


# ==================== PARKING SPOT EXCHANGE ====================
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Spot Type
    listing_type = db.Column(db.String(20), nullable=False)  # daily, semester, year, event
    
    # Location
    location_name = db.Column(db.String(200), nullable=False)  # "Lot A, Near Gym"
    distance_from_campus = db.Column(db.Numeric(5, 2))  # miles
    proximity_to_buildings = db.Column(db.Text)  # "5 min walk to library"
    
    # Availability
    available_from = db.Column(db.Date, nullable=False)
    available_until = db.Column(db.Date)
    days_available = db.Column(db.String(100))  # "Monday-Friday" or "Weekends only"
    time_available = db.Column(db.String(100))  # "8am-5pm" or "All day"
    
    # Pricing
    price_per_day = db.Column(db.Numeric(6, 2))
    price_per_semester = db.Column(db.Numeric(8, 2))
    negotiable = db.Column(db.Boolean, default=True)
    
    # Features
    covered = db.Column(db.Boolean, default=False)
    reserved = db.Column(db.Boolean, default=True)  # Reserved spot vs street parking
    security_features = db.Column(db.Text)  # "Gated, Camera surveillance"
    ev_charging = db.Column(db.Boolean, default=False)
    
    # Restrictions
    compact_only = db.Column(db.Boolean, default=False)
    oversized_ok = db.Column(db.Boolean, default=False)
    
    # Description
    description = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='available', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='parking_spots')


# ==================== TUTOR MARKETPLACE ====================
class TutorProfile(db.Model):
    __tablename__ = 'tutor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Tutor Info
    bio = db.Column(db.Text, nullable=False)
    major = db.Column(db.String(100))
    year = db.Column(db.String(20))  # Freshman, Sophomore, Junior, Senior, Graduate
    gpa = db.Column(db.Numeric(3, 2))
    
    # Subjects (JSON array)
    subjects = db.Column(db.Text, nullable=False)  # ["MATH 147", "PHYS 201", "CHEM 121"]
    
    # Availability
    availability = db.Column(db.Text)  # JSON: {"Monday": ["9am-12pm", "2pm-5pm"]}
    preferred_location = db.Column(db.String(200))  # "Library, Coffee shops, Online"
    offers_online = db.Column(db.Boolean, default=True)
    offers_in_person = db.Column(db.Boolean, default=True)
    
    # Pricing
    hourly_rate = db.Column(db.Numeric(6, 2), nullable=False)
    first_session_free = db.Column(db.Boolean, default=False)
    group_discount = db.Column(db.Boolean, default=False)
    
    # Experience
    tutoring_experience = db.Column(db.Text)  # Years, previous students, etc.
    certifications = db.Column(db.Text)  # Any relevant certifications
    
    # Ratings
    avg_rating = db.Column(db.Numeric(3, 2), default=0)
    total_sessions = db.Column(db.Integer, default=0)
    total_reviews = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)  # Admin verified
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='tutor_profile')


class TutoringSession(db.Model):
    __tablename__ = 'tutoring_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Session Details
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200))
    session_type = db.Column(db.String(20), default='individual')  # individual, group
    
    # Schedule
    scheduled_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    location = db.Column(db.String(200))
    is_online = db.Column(db.Boolean, default=False)
    
    # Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    
    # Review
    student_rating = db.Column(db.Integer)  # 1-5
    student_review = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='tutoring_sessions_given')
    student = db.relationship('User', foreign_keys=[student_id], backref='tutoring_sessions_received')


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
