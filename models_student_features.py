from extensions import db
from datetime import datetime
from sqlalchemy import Index

# ==================== TEXTBOOK EXCHANGE ====================
class TextbookListing(db.Model):
    __tablename__ = 'textbook_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Book Information
    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(200))
    isbn = db.Column(db.String(20), index=True)
    edition = db.Column(db.String(50))
    course_code = db.Column(db.String(20), index=True)  # e.g., "PSYCH 101"
    course_name = db.Column(db.String(200))
    
    # Listing Details
    condition = db.Column(db.String(50), nullable=False)  # New, Like New, Good, Fair, Poor
    price = db.Column(db.Numeric(10, 2), nullable=False)
    original_price = db.Column(db.Numeric(10, 2))
    description = db.Column(db.Text)
    
    # Images
    image_url_1 = db.Column(db.String(500))
    image_url_2 = db.Column(db.String(500))
    image_url_3 = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='available')  # available, pending, sold
    is_negotiable = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sold_at = db.Column(db.DateTime)
    views = db.Column(db.Integer, default=0)
    
    # Relationships
    seller = db.relationship('User', backref='textbook_listings', foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_textbook_course_status', 'course_code', 'status'),
        Index('idx_textbook_isbn_status', 'isbn', 'status'),
    )


class TextbookInterest(db.Model):
    __tablename__ = 'textbook_interests'
    
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('textbook_listings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text)
    offer_price = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== HOUSING REVIEWS ====================

# HousingListing model removed - duplicate exists in another file
# Original definition commented out to avoid SQLAlchemy conflicts

# class HousingListing(db.Model):
#     __tablename__ = 'housing_listings'
#     
#     id = db.Column(db.Integer, primary_key=True)
#     
    # Property Information
#     property_name = db.Column(db.String(200), nullable=False)
#     address = db.Column(db.String(300), nullable=False)
#     landlord_name = db.Column(db.String(200))
#     landlord_contact = db.Column(db.String(100))
#     
    # Details
#     property_type = db.Column(db.String(50))  # Apartment, House, Duplex, Room
#     bedrooms = db.Column(db.Integer)
#     bathrooms = db.Column(db.Numeric(3, 1))
#     rent_min = db.Column(db.Numeric(10, 2))
#     rent_max = db.Column(db.Numeric(10, 2))
#     
    # Amenities (JSON or comma-separated)
#     amenities = db.Column(db.Text)  # "Parking,Laundry,WiFi,Pets"
#     utilities_included = db.Column(db.Text)  # "Water,Trash"
#     
    # Location
#     distance_to_campus = db.Column(db.Numeric(5, 2))  # miles
#     latitude = db.Column(db.Numeric(10, 8))
#     longitude = db.Column(db.Numeric(11, 8))
#     
    # Ratings (calculated from reviews)
#     avg_rating = db.Column(db.Numeric(3, 2), default=0)
#     avg_safety_rating = db.Column(db.Numeric(3, 2), default=0)
#     avg_maintenance_rating = db.Column(db.Numeric(3, 2), default=0)
#     avg_value_rating = db.Column(db.Numeric(3, 2), default=0)
#     review_count = db.Column(db.Integer, default=0)
#     
    # Metadata
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
#     verified = db.Column(db.Boolean, default=False)
# 
# 
class HousingReview(db.Model):
    __tablename__ = 'housing_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('housing_listings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Ratings
    overall_rating = db.Column(db.Integer, nullable=False)  # 1-5
    safety_rating = db.Column(db.Integer)
    maintenance_rating = db.Column(db.Integer)
    value_rating = db.Column(db.Integer)
    landlord_rating = db.Column(db.Integer)
    
    # Review Content
    title = db.Column(db.String(200))
    review_text = db.Column(db.Text, nullable=False)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    
    # Details
    move_in_date = db.Column(db.Date)
    move_out_date = db.Column(db.Date)
    would_recommend = db.Column(db.Boolean)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    helpful_count = db.Column(db.Integer, default=0)
    verified_resident = db.Column(db.Boolean, default=False)
    
    # Relationships
    listing = db.relationship('HousingListing', backref='reviews')
    reviewer = db.relationship('User', backref='housing_reviews')


# ==================== STUDENT DISCOUNTS ====================
class StudentDiscount(db.Model):
    __tablename__ = 'student_discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Business Information
    business_name = db.Column(db.String(200), nullable=False, index=True)
    business_type = db.Column(db.String(50))  # Restaurant, Retail, Entertainment, Services
    address = db.Column(db.String(300))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(300))
    
    # Discount Details
    discount_description = db.Column(db.Text, nullable=False)
    discount_amount = db.Column(db.String(100))  # "10%", "$5 off", "Buy 1 Get 1"
    promo_code = db.Column(db.String(50))
    
    # Requirements
    verification_required = db.Column(db.Boolean, default=True)
    requirements = db.Column(db.Text)  # "Show student ID", "Use promo code"
    
    # Validity
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    days_valid = db.Column(db.String(100))  # "Monday-Friday", "Weekends"
    
    # Location
    is_local = db.Column(db.Boolean, default=True)
    is_online = db.Column(db.Boolean, default=False)
    distance_from_campus = db.Column(db.Numeric(5, 2))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    popularity_score = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    save_count = db.Column(db.Integer, default=0)


class DiscountUsage(db.Model):
    __tablename__ = 'discount_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    discount_id = db.Column(db.Integer, db.ForeignKey('student_discounts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    rating = db.Column(db.Integer)  # 1-5
    comment = db.Column(db.Text)


# ==================== GRADE DISTRIBUTION EXPLORER ====================
class GradeDistribution(db.Model):
    __tablename__ = 'grade_distributions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Course Information
    course_code = db.Column(db.String(20), nullable=False, index=True)
    course_name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), index=True)
    professor_name = db.Column(db.String(200), index=True)
    
    # Term
    semester = db.Column(db.String(20), nullable=False)  # "Fall 2024"
    year = db.Column(db.Integer, nullable=False)
    
    # Grade Counts
    grade_a = db.Column(db.Integer, default=0)
    grade_b = db.Column(db.Integer, default=0)
    grade_c = db.Column(db.Integer, default=0)
    grade_d = db.Column(db.Integer, default=0)
    grade_f = db.Column(db.Integer, default=0)
    grade_w = db.Column(db.Integer, default=0)  # Withdrawals
    
    # Statistics
    total_students = db.Column(db.Integer, nullable=False)
    gpa_average = db.Column(db.Numeric(3, 2))
    pass_rate = db.Column(db.Numeric(5, 2))  # Percentage
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    data_source = db.Column(db.String(50))  # "student_reported", "official", "aggregated"
    verified = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        Index('idx_grade_course_prof', 'course_code', 'professor_name'),
        Index('idx_grade_dept_semester', 'department', 'semester', 'year'),
    )


# ==================== PROFESSOR REVIEWS ====================
class ProfessorReview(db.Model):
    __tablename__ = 'professor_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Professor & Course
    professor_name = db.Column(db.String(200), nullable=False, index=True)
    department = db.Column(db.String(100), index=True)
    course_code = db.Column(db.String(20))
    course_name = db.Column(db.String(200))
    
    # Review by User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Ratings (1-5)
    overall_rating = db.Column(db.Integer, nullable=False)
    difficulty_rating = db.Column(db.Integer)  # 1=Easy, 5=Very Hard
    clarity_rating = db.Column(db.Integer)
    helpfulness_rating = db.Column(db.Integer)
    grading_fairness = db.Column(db.Integer)
    
    # Details
    semester_taken = db.Column(db.String(20))  # "Fall 2024"
    grade_received = db.Column(db.String(5))  # A, B, C, etc. (optional)
    attendance_mandatory = db.Column(db.Boolean)
    would_take_again = db.Column(db.Boolean)
    
    # Review Content
    review_text = db.Column(db.Text, nullable=False)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    tips = db.Column(db.Text)  # "Attend office hours", "Read before class"
    
    # Workload
    hours_per_week = db.Column(db.Integer)  # Study hours outside class
    textbook_required = db.Column(db.Boolean)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    helpful_count = db.Column(db.Integer, default=0)
    verified_student = db.Column(db.Boolean, default=False)
    
    # Relationships
    reviewer = db.relationship('User', backref='professor_reviews')
    
    __table_args__ = (
        Index('idx_prof_review_name_course', 'professor_name', 'course_code'),
    )


class ProfessorProfile(db.Model):
    __tablename__ = 'professor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    department = db.Column(db.String(100))
    office_location = db.Column(db.String(100))
    email = db.Column(db.String(150))
    
    # Aggregated Ratings
    avg_overall_rating = db.Column(db.Numeric(3, 2), default=0)
    avg_difficulty = db.Column(db.Numeric(3, 2), default=0)
    avg_clarity = db.Column(db.Numeric(3, 2), default=0)
    avg_helpfulness = db.Column(db.Numeric(3, 2), default=0)
    review_count = db.Column(db.Integer, default=0)
    would_take_again_percent = db.Column(db.Numeric(5, 2), default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== CAMPUS SERVICE WAIT TIMES ====================
class CampusService(db.Model):
    __tablename__ = 'campus_services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), index=True)  # Dining, Gym, Library, Health, Admin
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    
    # Current Status
    current_wait_time = db.Column(db.Integer, default=0)  # minutes
    current_capacity = db.Column(db.String(20))  # "Low", "Medium", "High"
    is_open = db.Column(db.Boolean, default=True)
    
    # Hours
    hours_monday = db.Column(db.String(50))
    hours_tuesday = db.Column(db.String(50))
    hours_wednesday = db.Column(db.String(50))
    hours_thursday = db.Column(db.String(50))
    hours_friday = db.Column(db.String(50))
    hours_saturday = db.Column(db.String(50))
    hours_sunday = db.Column(db.String(50))
    
    # Statistics
    avg_wait_time = db.Column(db.Integer, default=0)
    peak_hours = db.Column(db.String(200))  # "11am-1pm, 5pm-7pm"
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


class ServiceWaitReport(db.Model):
    __tablename__ = 'service_wait_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('campus_services.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    wait_time = db.Column(db.Integer)  # minutes reported
    capacity_level = db.Column(db.String(20))  # "empty", "light", "moderate", "busy", "packed"
    
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    service = db.relationship('CampusService', backref='wait_reports')


# ==================== STUDENT EVENT CALENDAR ====================
class StudentEvent(db.Model):
    __tablename__ = 'student_events'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event Information
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))  # Social, Academic, Sports, Club, Greek Life
    category = db.Column(db.String(50))  # Party, Study Group, Fundraiser, Competition
    
    # Organizer
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_name = db.Column(db.String(200))  # Club/Org name
    
    # Date & Time
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(100))  # "Weekly on Tuesdays"
    
    # Location
    location_name = db.Column(db.String(200))
    address = db.Column(db.String(300))
    is_virtual = db.Column(db.Boolean, default=False)
    virtual_link = db.Column(db.String(500))
    
    # Details
    is_free = db.Column(db.Boolean, default=True)
    cost = db.Column(db.Numeric(10, 2))
    capacity = db.Column(db.Integer)
    rsvp_required = db.Column(db.Boolean, default=False)
    registration_link = db.Column(db.String(500))
    
    # Requirements
    age_restriction = db.Column(db.String(50))
    students_only = db.Column(db.Boolean, default=True)
    
    # Images
    image_url = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='upcoming')  # upcoming, ongoing, completed, cancelled
    is_featured = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    rsvp_count = db.Column(db.Integer, default=0)
    
    # Relationships
    organizer = db.relationship('User', backref='organized_events', foreign_keys=[organizer_id])
    
    __table_args__ = (
        Index('idx_event_type_date', 'event_type', 'start_datetime'),
        Index('idx_event_status_date', 'status', 'start_datetime'),
    )


class EventRSVP(db.Model):
    __tablename__ = 'event_rsvps'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('student_events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='going')  # going, interested, not_going
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('StudentEvent', backref='rsvps')
    user = db.relationship('User', backref='event_rsvps')


# ==================== COURSE MATERIAL LIBRARY ====================
class CourseMaterial(db.Model):
    __tablename__ = 'course_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Course Information
    course_code = db.Column(db.String(20), nullable=False, index=True)
    course_name = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), index=True)
    professor_name = db.Column(db.String(200))
    semester = db.Column(db.String(20))  # "Fall 2024"
    
    # Material Information
    title = db.Column(db.String(300), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)  # Notes, Study Guide, Exam, Syllabus, Slides
    description = db.Column(db.Text)
    
    # File/Link
    file_url = db.Column(db.String(500))  # Cloud storage link
    file_type = db.Column(db.String(20))  # PDF, DOCX, PPTX
    file_size_mb = db.Column(db.Numeric(10, 2))
    external_link = db.Column(db.String(500))  # For external resources
    
    # Uploader
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Quality Metrics
    downloads = db.Column(db.Integer, default=0)
    rating = db.Column(db.Numeric(3, 2), default=0)
    rating_count = db.Column(db.Integer, default=0)
    
    # Tags
    tags = db.Column(db.Text)  # "exam1,midterm,chapter3,formulas"
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    flagged = db.Column(db.Boolean, default=False)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_materials')
    
    __table_args__ = (
        Index('idx_material_course_type', 'course_code', 'material_type'),
        Index('idx_material_dept_semester', 'department', 'semester'),
    )


class MaterialRating(db.Model):
    __tablename__ = 'material_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('course_materials.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    material = db.relationship('CourseMaterial', backref='ratings')
    rater = db.relationship('User', backref='material_ratings')
