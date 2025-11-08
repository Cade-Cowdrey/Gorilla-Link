"""
Advanced Growth Features - Enterprise-Grade Models
Best-in-class features for PSU students
"""

# Determine if we're using PostgreSQL or SQLite
import os
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///pittstate_connect_local.db')
USE_POSTGRES = DATABASE_URL.startswith('postgresql')

from extensions import db
from datetime import datetime
from sqlalchemy import Index
import json

# ==================== EMERGENCY RESOURCES & CRISIS RELIEF CENTER ====================

class EmergencyResource(db.Model):
    """Comprehensive emergency resource directory"""
    __tablename__ = 'emergency_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Resource Information
    resource_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: financial_aid, food_assistance, housing_emergency, mental_health, 
    # medical, legal_aid, domestic_violence, substance_abuse, academic_crisis, technology
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    detailed_info = db.Column(db.Text)
    
    # Contact Information
    phone_number = db.Column(db.String(20))
    emergency_hotline = db.Column(db.String(20))
    email = db.Column(db.String(150))
    website = db.Column(db.String(500))
    
    # Location
    physical_address = db.Column(db.String(300))
    building_room = db.Column(db.String(100))
    map_coordinates = db.Column(db.String(100))  # lat,long for mapping
    
    # Availability
    hours_of_operation = db.Column(db.Text)  # JSON: {"Monday": "8am-5pm", ...}
    is_24_7 = db.Column(db.Boolean, default=False)
    after_hours_contact = db.Column(db.String(200))
    
    # Priority & Visibility
    is_crisis_resource = db.Column(db.Boolean, default=False)  # Show prominently
    priority_level = db.Column(db.Integer, default=0)  # Higher = more important
    
    # Eligibility & Requirements
    eligibility_criteria = db.Column(db.Text)
    required_documents = db.Column(db.Text)
    application_process = db.Column(db.Text)
    
    # Languages & Accessibility
    languages_supported = db.Column(db.String(200))  # "English, Spanish, ASL"
    accessibility_features = db.Column(db.Text)
    
    # External Links
    appointment_booking_url = db.Column(db.String(500))
    online_form_url = db.Column(db.String(500))
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_psu_operated = db.Column(db.Boolean, default=True)
    last_verified = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage Tracking
    view_count = db.Column(db.Integer, default=0)
    referral_count = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        Index('idx_resource_type_priority', 'resource_type', 'priority_level'),
        Index('idx_crisis_active', 'is_crisis_resource', 'is_active'),
    )


class CrisisIntakeForm(db.Model):
    """Smart intake forms for crisis situations"""
    __tablename__ = 'crisis_intake_forms'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Crisis Type
    crisis_type = db.Column(db.String(50), nullable=False, index=True)
    # financial, housing, food_insecurity, mental_health, medical, 
    # academic, family_emergency, safety_concern, other
    
    urgency_level = db.Column(db.String(20), nullable=False)  # immediate, urgent, moderate, low
    
    # Detailed Information
    situation_description = db.Column(db.Text, nullable=False)
    immediate_needs = db.Column(db.Text)
    
    # Current Status
    has_safe_housing = db.Column(db.Boolean)
    has_food_access = db.Column(db.Boolean)
    has_transportation = db.Column(db.Boolean)
    has_medical_care = db.Column(db.Boolean)
    has_financial_resources = db.Column(db.Boolean)
    
    # Additional Details
    dependents = db.Column(db.Integer, default=0)
    estimated_cost_needed = db.Column(db.Numeric(10, 2))
    timeline_needed = db.Column(db.String(100))  # "Within 24 hours", "This week", etc.
    
    # Previous Assistance
    previous_help_received = db.Column(db.Text)
    other_resources_tried = db.Column(db.Text)
    
    # Contact Preferences
    preferred_contact_method = db.Column(db.String(20))  # phone, email, in_person
    best_time_to_contact = db.Column(db.String(100))
    secondary_contact_name = db.Column(db.String(200))
    secondary_contact_phone = db.Column(db.String(20))
    
    # Routing & Assignment
    routed_to_department = db.Column(db.String(100))
    assigned_to_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    auto_matched_resources = db.Column(db.Text)  # JSON array of resource IDs
    
    # Status Tracking
    status = db.Column(db.String(30), default='pending', index=True)
    # pending, under_review, assistance_provided, referred_external, resolved, closed
    
    resolution_notes = db.Column(db.Text)
    assistance_provided = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    reviewed_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    
    # Privacy
    consent_to_share_info = db.Column(db.Boolean, default=False)
    is_confidential = db.Column(db.Boolean, default=True)
    
    # Relationships
    submitter = db.relationship('User', foreign_keys=[user_id], backref='crisis_intakes')
    assigned_staff = db.relationship('User', foreign_keys=[assigned_to_staff_id], backref='assigned_crisis_cases')


class CommunityFundDonation(db.Model):
    """Alumni/sponsor donations for student emergencies"""
    __tablename__ = 'community_fund_donations'
    
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Donation Details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    donation_type = db.Column(db.String(30), default='one_time')  # one_time, recurring_monthly, recurring_annual
    
    # Designation
    designated_purpose = db.Column(db.String(100))  # emergency_fund, food_pantry, housing, textbooks, general
    student_recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # If donating to specific student
    
    # Donor Information
    donor_name = db.Column(db.String(200))  # For recognition (if not anonymous)
    is_anonymous = db.Column(db.Boolean, default=False)
    donor_type = db.Column(db.String(30))  # alumni, parent, community_member, corporation, foundation
    
    # Recognition
    public_message = db.Column(db.Text)  # Optional message to students
    recognition_level = db.Column(db.String(50))  # bronze, silver, gold, platinum (based on amount)
    
    # Payment Info
    payment_method = db.Column(db.String(30))  # credit_card, bank_transfer, check, payroll_deduction
    payment_status = db.Column(db.String(30), default='pending')  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100))
    
    # Tax & Receipts
    is_tax_deductible = db.Column(db.Boolean, default=True)
    receipt_sent = db.Column(db.Boolean, default=False)
    receipt_sent_at = db.Column(db.DateTime)
    
    # Impact Tracking
    students_helped = db.Column(db.Integer, default=0)
    impact_stories = db.Column(db.Text)  # JSON array of impact narratives
    
    # Timestamps
    donated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    donor = db.relationship('User', foreign_keys=[donor_id], backref='donations_made')
    recipient = db.relationship('User', foreign_keys=[student_recipient_id], backref='donations_received')


# ==================== RESEARCH PROJECT MARKETPLACE ====================

class ResearchProject(db.Model):
    """Faculty research opportunities for students"""
    __tablename__ = 'research_projects'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Project Information
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    research_area = db.Column(db.String(100), nullable=False, index=True)
    # STEM, Social_Sciences, Humanities, Business, Health_Sciences, Education, Arts
    
    specific_field = db.Column(db.String(100))  # Biology, Computer Science, Psychology, etc.
    
    # Project Details
    project_type = db.Column(db.String(50))  # lab_research, field_research, data_analysis, literature_review, creative
    project_duration = db.Column(db.String(50))  # semester, summer, academic_year, 1-2_years
    time_commitment = db.Column(db.String(100))  # "10 hours/week", "Flexible", "20+ hours/week"
    
    # Requirements
    required_skills = db.Column(db.Text)  # JSON array: ["Python", "Statistical Analysis", "Lab Experience"]
    preferred_skills = db.Column(db.Text)  # JSON array
    required_courses = db.Column(db.Text)  # JSON array: ["BIO 101", "CHEM 121"]
    minimum_gpa = db.Column(db.Numeric(3, 2))
    class_standing = db.Column(db.String(100))  # "Sophomore+", "Junior/Senior", "Graduate students"
    
    # Opportunities Offered
    positions_available = db.Column(db.Integer, default=1)
    current_team_size = db.Column(db.Integer, default=0)
    
    compensation_type = db.Column(db.String(50))  # credit, stipend, volunteer, work_study, combination
    credit_hours = db.Column(db.Integer)
    stipend_amount = db.Column(db.Numeric(10, 2))
    stipend_frequency = db.Column(db.String(30))  # hourly, weekly, monthly, semester
    
    # Learning Outcomes
    skills_students_will_gain = db.Column(db.Text)  # JSON array
    publication_potential = db.Column(db.Boolean, default=False)
    conference_presentation_potential = db.Column(db.Boolean, default=False)
    thesis_eligible = db.Column(db.Boolean, default=False)
    
    # Project Timeline
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    application_deadline = db.Column(db.Date, index=True)
    is_ongoing = db.Column(db.Boolean, default=False)
    
    # Funding & Grants
    is_grant_funded = db.Column(db.Boolean, default=False)
    grant_name = db.Column(db.String(200))
    funding_source = db.Column(db.String(200))
    total_project_budget = db.Column(db.Numeric(12, 2))
    
    # Collaboration
    collaborating_departments = db.Column(db.Text)  # JSON array
    external_partners = db.Column(db.Text)  # Industry partners, other universities
    
    # Application Process
    application_instructions = db.Column(db.Text)
    required_documents = db.Column(db.Text)  # resume, transcript, cover_letter, writing_sample
    interview_required = db.Column(db.Boolean, default=False)
    
    # Contact
    contact_email = db.Column(db.String(150))
    contact_phone = db.Column(db.String(20))
    office_location = db.Column(db.String(200))
    office_hours = db.Column(db.String(200))
    
    # Status & Visibility
    status = db.Column(db.String(30), default='active', index=True)
    # active, filled, paused, completed, cancelled
    is_featured = db.Column(db.Boolean, default=False)
    
    # Engagement Metrics
    view_count = db.Column(db.Integer, default=0)
    application_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    faculty = db.relationship('User', foreign_keys=[faculty_id], backref='research_projects')
    
    __table_args__ = (
        Index('idx_research_area_status', 'research_area', 'status'),
        Index('idx_deadline', 'application_deadline'),
    )


class ResearchApplication(db.Model):
    """Student applications to research projects"""
    __tablename__ = 'research_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('research_projects.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Application Materials
    cover_letter = db.Column(db.Text)
    relevant_coursework = db.Column(db.Text)
    relevant_experience = db.Column(db.Text)
    skills_list = db.Column(db.Text)  # JSON array
    
    # Student Background
    major = db.Column(db.String(100))
    minor = db.Column(db.String(100))
    gpa = db.Column(db.Numeric(3, 2))
    class_standing = db.Column(db.String(30))  # Freshman, Sophomore, Junior, Senior, Graduate
    
    # Availability
    available_hours_per_week = db.Column(db.Integer)
    preferred_start_date = db.Column(db.Date)
    availability_notes = db.Column(db.Text)
    
    # References
    reference_name_1 = db.Column(db.String(200))
    reference_email_1 = db.Column(db.String(150))
    reference_name_2 = db.Column(db.String(200))
    reference_email_2 = db.Column(db.String(150))
    
    # AI Matching Score
    match_score = db.Column(db.Numeric(5, 2))  # 0-100, calculated by AI matchmaker
    match_explanation = db.Column(db.Text)  # Why this student is a good fit
    
    # Application Status
    status = db.Column(db.String(30), default='pending', index=True)
    # pending, under_review, interview_scheduled, accepted, rejected, withdrawn
    
    faculty_notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    
    # Interview
    interview_scheduled = db.Column(db.DateTime)
    interview_location = db.Column(db.String(200))
    interview_notes = db.Column(db.Text)
    
    # Decision
    decision_date = db.Column(db.DateTime)
    acceptance_deadline = db.Column(db.DateTime)
    student_accepted_offer = db.Column(db.Boolean)
    
    # Timestamps
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('ResearchProject', backref='applications')
    student = db.relationship('User', backref='research_applications')
    
    __table_args__ = (
        Index('idx_project_status', 'project_id', 'status'),
    )


class ResearchTeamMember(db.Model):
    """Active research team members"""
    __tablename__ = 'research_team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('research_projects.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    role = db.Column(db.String(100))  # Research Assistant, Lab Technician, Data Analyst, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    is_active = db.Column(db.Boolean, default=True, index=True)
    hours_contributed = db.Column(db.Integer, default=0)
    
    # Achievements
    publications_coauthored = db.Column(db.Integer, default=0)
    conferences_attended = db.Column(db.Integer, default=0)
    presentations_given = db.Column(db.Integer, default=0)
    
    # Performance
    faculty_rating = db.Column(db.Integer)  # 1-5
    faculty_feedback = db.Column(db.Text)
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('ResearchProject', backref='team_members')
    student = db.relationship('User', backref='research_team_memberships')


# ==================== WORKFORCE & EMPLOYER ALIGNMENT HUB ====================

class CareerPathway(db.Model):
    """Career alignment for PSU majors"""
    __tablename__ = 'career_pathways'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Academic Program
    major = db.Column(db.String(100), nullable=False, index=True)
    concentration = db.Column(db.String(100))
    degree_level = db.Column(db.String(30))  # Associate, Bachelor, Master, Doctoral
    
    # Career Information
    career_title = db.Column(db.String(200), nullable=False)
    career_field = db.Column(db.String(100))  # Technology, Healthcare, Business, Education, etc.
    industry = db.Column(db.String(100))
    
    # Job Market Data
    national_median_salary = db.Column(db.Numeric(10, 2))
    regional_median_salary = db.Column(db.Numeric(10, 2))  # Kansas/Missouri region
    entry_level_salary = db.Column(db.Numeric(10, 2))
    experienced_salary = db.Column(db.Numeric(10, 2))
    
    # Employment Outlook
    job_growth_rate = db.Column(db.Numeric(5, 2))  # % annual growth
    employment_outlook = db.Column(db.String(30))  # excellent, good, average, declining
    openings_per_year_national = db.Column(db.Integer)
    openings_per_year_regional = db.Column(db.Integer)
    
    # Skills Alignment
    required_skills = db.Column(db.Text)  # JSON array of skills
    psu_courses_that_teach_skills = db.Column(db.Text)  # JSON: {"Python": ["CS 101", "CS 201"]}
    skill_gaps = db.Column(db.Text)  # Skills needed but not in curriculum
    
    # Certifications & Credentials
    recommended_certifications = db.Column(db.Text)  # JSON array
    professional_licenses = db.Column(db.Text)  # JSON array
    
    # Career Progression
    typical_career_progression = db.Column(db.Text)  # JSON array of roles over time
    years_to_senior_level = db.Column(db.Integer)
    
    # Top Employers
    top_employers = db.Column(db.Text)  # JSON array of company names
    psu_alumni_at_employers = db.Column(db.Text)  # JSON: {"Boeing": 45, "Cerner": 32}
    
    # Geographic Data
    top_hiring_cities = db.Column(db.Text)  # JSON array
    remote_work_availability = db.Column(db.String(30))  # high, medium, low, none
    
    # Data Sources & Freshness
    data_source = db.Column(db.String(100))  # BLS, LinkedIn, Glassdoor, PSU Career Services
    last_updated = db.Column(db.DateTime, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_major_updated', 'major', 'last_updated'),
    )


class SkillDemandForecast(db.Model):
    """Real-time skill demand in job market"""
    __tablename__ = 'skill_demand_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    skill_name = db.Column(db.String(100), nullable=False, index=True)
    skill_category = db.Column(db.String(50))  # technical, soft_skill, certification, language
    
    # Demand Metrics
    current_demand_score = db.Column(db.Integer)  # 0-100
    trend = db.Column(db.String(20))  # rising, stable, declining
    year_over_year_change = db.Column(db.Numeric(5, 2))  # % change
    
    # Regional Data
    regional_job_postings = db.Column(db.Integer)  # Jobs mentioning this skill in KS/MO
    national_job_postings = db.Column(db.Integer)
    
    # Salary Premium
    avg_salary_with_skill = db.Column(db.Numeric(10, 2))
    avg_salary_without_skill = db.Column(db.Numeric(10, 2))
    salary_premium_percentage = db.Column(db.Numeric(5, 2))
    
    # PSU Context
    psu_courses_teaching_skill = db.Column(db.Text)  # JSON array
    students_with_skill = db.Column(db.Integer)
    
    # Related Skills
    complementary_skills = db.Column(db.Text)  # JSON array (skills often listed together)
    
    # Forecast (next 12 months)
    forecasted_demand = db.Column(db.String(30))  # increasing, stable, decreasing
    forecasted_change = db.Column(db.Numeric(5, 2))  # Expected % change
    
    # Top Industries
    top_industries_needing_skill = db.Column(db.Text)  # JSON array
    
    # Data Metadata
    data_date = db.Column(db.Date, index=True)
    data_source = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_skill_date', 'skill_name', 'data_date'),
    )


class FacultyIndustryCollaboration(db.Model):
    """Track PSU faculty-industry partnerships"""
    __tablename__ = 'faculty_industry_collaborations'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Company Information
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # startup, small, medium, large, enterprise
    
    # Collaboration Details
    collaboration_type = db.Column(db.String(50))
    # research_partnership, curriculum_development, internship_program, 
    # guest_lectures, sponsored_projects, equipment_donation, advisory_board
    
    project_title = db.Column(db.String(300))
    description = db.Column(db.Text)
    
    # Financials
    funding_amount = db.Column(db.Numeric(12, 2))
    in_kind_contributions = db.Column(db.Text)  # Equipment, software licenses, etc.
    
    # Timeline
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_ongoing = db.Column(db.Boolean, default=False)
    
    # Student Impact
    students_involved = db.Column(db.Integer, default=0)
    internships_created = db.Column(db.Integer, default=0)
    jobs_created = db.Column(db.Integer, default=0)
    
    # Academic Impact
    courses_enhanced = db.Column(db.Text)  # JSON array of course codes
    equipment_acquired = db.Column(db.Text)
    publications_resulting = db.Column(db.Integer, default=0)
    
    # Contact
    company_contact_name = db.Column(db.String(200))
    company_contact_email = db.Column(db.String(150))
    company_contact_phone = db.Column(db.String(20))
    
    # Status
    status = db.Column(db.String(30), default='active')  # active, completed, paused, cancelled
    
    # Public Visibility
    is_public = db.Column(db.Boolean, default=True)
    featured_on_website = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    faculty = db.relationship('User', backref='industry_collaborations')


# ==================== SMART HOUSING AI ====================

class HousingListing(db.Model):
    """Comprehensive off-campus housing database"""
    __tablename__ = 'housing_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # If landlord has account
    
    # Property Basics
    property_name = db.Column(db.String(200))
    address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), default='Pittsburg')
    state = db.Column(db.String(2), default='KS')
    zip_code = db.Column(db.String(10))
    
    # Property Type
    property_type = db.Column(db.String(50), nullable=False)
    # apartment, house, duplex, studio, townhouse, room_rental
    
    # Space Details
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Numeric(3, 1), nullable=False)
    square_feet = db.Column(db.Integer)
    
    # Rent & Costs
    monthly_rent = db.Column(db.Numeric(10, 2), nullable=False, index=True)
    security_deposit = db.Column(db.Numeric(10, 2))
    application_fee = db.Column(db.Numeric(10, 2))
    
    # Utilities
    utilities_included = db.Column(db.Text)  # "Water, Trash, Internet"
    avg_monthly_utilities = db.Column(db.Numeric(8, 2))
    utilities_paid_by_tenant = db.Column(db.Text)
    
    # Lease Terms
    lease_length = db.Column(db.String(50))  # "12 months", "Academic year", "Month-to-month"
    available_from = db.Column(db.Date, index=True)
    available_until = db.Column(db.Date)
    
    # Features & Amenities
    furnished = db.Column(db.Boolean, default=False)
    parking_included = db.Column(db.Boolean, default=False)
    parking_spaces = db.Column(db.Integer)
    laundry = db.Column(db.String(50))  # in_unit, on_site, coin_operated, none
    air_conditioning = db.Column(db.Boolean, default=False)
    heating_type = db.Column(db.String(50))
    
    # Building Amenities
    has_pool = db.Column(db.Boolean, default=False)
    has_gym = db.Column(db.Boolean, default=False)
    has_common_area = db.Column(db.Boolean, default=False)
    has_study_room = db.Column(db.Boolean, default=False)
    has_elevator = db.Column(db.Boolean, default=False)
    
    # Pet Policy
    pets_allowed = db.Column(db.Boolean, default=False)
    pet_types_allowed = db.Column(db.String(100))  # "Cats, Small dogs"
    pet_deposit = db.Column(db.Numeric(10, 2))
    pet_rent = db.Column(db.Numeric(10, 2))
    
    # Distance & Transportation
    distance_to_campus_miles = db.Column(db.Numeric(5, 2))
    walking_time_minutes = db.Column(db.Integer)
    biking_time_minutes = db.Column(db.Integer)
    driving_time_minutes = db.Column(db.Integer)
    on_shuttle_route = db.Column(db.Boolean, default=False)
    shuttle_stop_name = db.Column(db.String(200))
    
    # Neighborhood
    neighborhood = db.Column(db.String(100))
    walkability_score = db.Column(db.Integer)  # 0-100
    safety_rating = db.Column(db.Numeric(3, 1))  # 1-5 stars
    noise_level = db.Column(db.String(20))  # quiet, moderate, noisy
    
    # Nearby Amenities (distances in miles)
    nearest_grocery_distance = db.Column(db.Numeric(5, 2))
    nearest_restaurant_distance = db.Column(db.Numeric(5, 2))
    nearest_bus_stop_distance = db.Column(db.Numeric(5, 2))
    
    # Requirements
    minimum_credit_score = db.Column(db.Integer)
    income_requirement_multiplier = db.Column(db.Numeric(3, 1))  # e.g., 3x rent
    requires_cosigner = db.Column(db.Boolean, default=False)
    background_check_required = db.Column(db.Boolean, default=True)
    
    # Contact
    landlord_name = db.Column(db.String(200))
    landlord_company = db.Column(db.String(200))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(150))
    website = db.Column(db.String(500))
    
    # Application Process
    application_url = db.Column(db.String(500))
    virtual_tour_url = db.Column(db.String(500))
    in_person_tours_available = db.Column(db.Boolean, default=True)
    
    # Media
    photos = db.Column(db.Text)  # JSON array of image URLs
    floor_plan_url = db.Column(db.String(500))
    video_tour_url = db.Column(db.String(500))
    
    # AI Recommendations
    recommended_for_freshmen = db.Column(db.Boolean, default=False)
    recommended_for_international = db.Column(db.Boolean, default=False)
    recommended_for_graduate = db.Column(db.Boolean, default=False)
    
    # Affordability Metrics (calculated)
    affordability_index = db.Column(db.Numeric(5, 2))  # 0-100, higher = more affordable
    total_monthly_cost = db.Column(db.Numeric(10, 2))  # Rent + avg utilities
    
    # Status
    status = db.Column(db.String(30), default='available', index=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Engagement
    view_count = db.Column(db.Integer, default=0)
    inquiry_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified = db.Column(db.DateTime)
    
    landlord = db.relationship('User', backref='housing_listings')
    
    __table_args__ = (
        Index('idx_rent_available', 'monthly_rent', 'status'),
        Index('idx_bedrooms_rent', 'bedrooms', 'monthly_rent'),
        {'extend_existing': True}
    )


class RoommateFinder(db.Model):
    """PSU-verified roommate profiles"""
    __tablename__ = 'roommate_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Basic Info
    looking_for = db.Column(db.String(20), nullable=False)  # roommate, housing_and_roommate
    move_in_date = db.Column(db.Date, index=True)
    lease_length_preference = db.Column(db.String(50))
    
    # Budget
    max_monthly_rent = db.Column(db.Numeric(10, 2), nullable=False)
    max_total_cost = db.Column(db.Numeric(10, 2))
    
    # Housing Preferences
    preferred_bedrooms = db.Column(db.Integer)
    preferred_property_types = db.Column(db.Text)  # JSON array
    must_have_parking = db.Column(db.Boolean, default=False)
    must_have_laundry = db.Column(db.Boolean, default=False)
    max_distance_to_campus = db.Column(db.Numeric(5, 2))
    
    # Lifestyle
    sleep_schedule = db.Column(db.String(30))  # early_bird, night_owl, varies
    typical_bedtime = db.Column(db.String(20))  # "10-11pm", "After midnight", etc.
    cleanliness_level = db.Column(db.Integer)  # 1-5, 1=messy, 5=very clean
    noise_tolerance = db.Column(db.String(20))  # quiet, moderate, lively
    
    # Social Preferences
    social_level = db.Column(db.String(30))  # introverted, balanced, extroverted
    guests_frequency = db.Column(db.String(30))  # rarely, occasionally, frequently
    hosting_parties = db.Column(db.String(30))  # never, occasionally, often
    
    # Habits
    smoker = db.Column(db.Boolean, default=False)
    drinks_alcohol = db.Column(db.Boolean)
    has_pets = db.Column(db.Boolean, default=False)
    pet_types = db.Column(db.String(100))
    comfortable_with_pets = db.Column(db.Boolean)
    
    # Academic/Work
    major = db.Column(db.String(100))
    class_standing = db.Column(db.String(30))
    study_habits = db.Column(db.String(50))  # study_at_home, study_on_campus, varies
    work_schedule = db.Column(db.String(100))
    
    # Interests & Hobbies
    interests = db.Column(db.Text)  # JSON array
    music_preferences = db.Column(db.Text)
    
    # About Me
    bio = db.Column(db.Text, nullable=False)
    fun_fact = db.Column(db.Text)
    
    # Deal Breakers
    deal_breakers = db.Column(db.Text)  # Things absolutely not okay
    must_haves = db.Column(db.Text)  # Non-negotiables
    
    # Contact Preferences
    preferred_contact = db.Column(db.String(20))  # message, email, phone
    
    # AI Matching
    personality_profile = db.Column(db.Text)  # JSON from personality assessment
    compatibility_preferences = db.Column(db.Text)  # JSON of weighted preferences
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Engagement
    profile_views = db.Column(db.Integer, default=0)
    match_requests_sent = db.Column(db.Integer, default=0)
    match_requests_received = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='roommate_profile')


class RoommateMatch(db.Model):
    """AI-generated roommate compatibility matches"""
    __tablename__ = 'roommate_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # AI Compatibility Score
    compatibility_score = db.Column(db.Numeric(5, 2), nullable=False)  # 0-100
    
    # Compatibility Breakdown
    lifestyle_compatibility = db.Column(db.Numeric(5, 2))
    schedule_compatibility = db.Column(db.Numeric(5, 2))
    cleanliness_compatibility = db.Column(db.Numeric(5, 2))
    social_compatibility = db.Column(db.Numeric(5, 2))
    budget_compatibility = db.Column(db.Numeric(5, 2))
    
    # Shared Interests
    shared_interests = db.Column(db.Text)  # JSON array
    shared_majors_or_fields = db.Column(db.Boolean)
    
    # AI Explanation
    why_good_match = db.Column(db.Text)  # AI-generated explanation
    potential_conflicts = db.Column(db.Text)  # Things to discuss
    
    # Match Status
    status = db.Column(db.String(30), default='suggested')
    # suggested, user1_interested, user2_interested, both_interested, 
    # messaging, not_interested, matched
    
    # Interaction
    user1_viewed = db.Column(db.Boolean, default=False)
    user2_viewed = db.Column(db.Boolean, default=False)
    user1_interested = db.Column(db.Boolean)
    user2_interested = db.Column(db.Boolean)
    
    # Notes
    user1_notes = db.Column(db.Text)
    user2_notes = db.Column(db.Text)
    
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user1 = db.relationship('User', foreign_keys=[user1_id], backref='roommate_matches_as_user1')
    user2 = db.relationship('User', foreign_keys=[user2_id], backref='roommate_matches_as_user2')
    
    __table_args__ = (
        Index('idx_users_score', 'user1_id', 'user2_id', 'compatibility_score'),
    )


# ==================== GLOBAL PSU COLLABORATION NETWORK ====================

class InternationalStudentProfile(db.Model):
    """International student resources and tracking"""
    __tablename__ = 'international_student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Origin Information
    home_country = db.Column(db.String(100), nullable=False, index=True)
    home_city = db.Column(db.String(100))
    native_language = db.Column(db.String(100))
    additional_languages = db.Column(db.Text)  # JSON array
    
    # Visa Status
    visa_type = db.Column(db.String(20))  # F-1, J-1, etc.
    visa_expiration = db.Column(db.Date)
    i20_expiration = db.Column(db.Date)
    opt_status = db.Column(db.String(50))  # pre_completion, post_completion, stem_extension, none
    opt_expiration = db.Column(db.Date)
    
    # Travel & Authorization
    last_entry_date = db.Column(db.Date)
    travel_authorization_status = db.Column(db.String(30))  # valid, needs_renewal, expired
    
    # Academic
    program_start_date = db.Column(db.Date)
    expected_graduation = db.Column(db.Date)
    maintains_full_time_status = db.Column(db.Boolean, default=True)
    
    # Support Needs
    needs_cultural_adjustment_support = db.Column(db.Boolean)
    needs_language_support = db.Column(db.Boolean)
    needs_visa_guidance = db.Column(db.Boolean)
    needs_tax_assistance = db.Column(db.Boolean)
    needs_employment_authorization_help = db.Column(db.Boolean)
    
    # Mentor Assignment
    has_mentor = db.Column(db.Boolean, default=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    mentor_match_date = db.Column(db.Date)
    
    # Cultural Engagement
    cultural_events_attended = db.Column(db.Integer, default=0)
    wants_to_share_culture = db.Column(db.Boolean, default=False)
    willing_to_mentor_new_students = db.Column(db.Boolean, default=False)
    
    # Emergency Contact (home country)
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_relationship = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(30))
    emergency_contact_email = db.Column(db.String(150))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[user_id], backref='international_profile')
    mentor = db.relationship('User', foreign_keys=[mentor_id], backref='international_mentees')


class GlobalAlumniMapping(db.Model):
    """Track PSU alumni worldwide"""
    __tablename__ = 'global_alumni_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Current Location
    current_country = db.Column(db.String(100), nullable=False, index=True)
    current_city = db.Column(db.String(100), nullable=False)
    current_state_province = db.Column(db.String(100))
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    
    # PSU History
    graduation_year = db.Column(db.Integer, index=True)
    degree_earned = db.Column(db.String(100))
    major = db.Column(db.String(100))
    
    # Current Professional Status
    current_employer = db.Column(db.String(200))
    current_job_title = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    years_in_current_role = db.Column(db.Integer)
    
    # Willingness to Help
    open_to_networking = db.Column(db.Boolean, default=False)
    offers_career_advice = db.Column(db.Boolean, default=False)
    offers_informational_interviews = db.Column(db.Boolean, default=False)
    can_help_with_relocation = db.Column(db.Boolean, default=False)
    speaks_languages = db.Column(db.Text)  # JSON array
    
    # Visibility Preferences
    show_on_public_map = db.Column(db.Boolean, default=False)
    show_employer = db.Column(db.Boolean, default=True)
    show_exact_location = db.Column(db.Boolean, default=False)  # vs just city
    
    # Engagement
    last_updated_location = db.Column(db.DateTime)
    profile_views = db.Column(db.Integer, default=0)
    connection_requests = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    alumni = db.relationship('User', backref='alumni_location')
    
    __table_args__ = (
        Index('idx_country_city', 'current_country', 'current_city'),
    )


class VirtualExchangeProgram(db.Model):
    """Virtual exchange with partner universities"""
    __tablename__ = 'virtual_exchange_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Program Information
    program_name = db.Column(db.String(200), nullable=False)
    program_type = db.Column(db.String(50))
    # collaborative_research, joint_course, cultural_exchange, 
    # language_exchange, faculty_collaboration, student_project
    
    description = db.Column(db.Text, nullable=False)
    
    # Partner Institution
    partner_university = db.Column(db.String(200), nullable=False)
    partner_country = db.Column(db.String(100), nullable=False)
    partner_city = db.Column(db.String(100))
    partner_department = db.Column(db.String(200))
    
    # Academic Details
    subject_area = db.Column(db.String(100))
    course_code_psu = db.Column(db.String(20))
    credit_hours = db.Column(db.Integer)
    academic_level = db.Column(db.String(30))  # undergraduate, graduate, both
    
    # Program Structure
    duration = db.Column(db.String(50))  # "8 weeks", "Full semester", "Year-long"
    meeting_frequency = db.Column(db.String(100))  # "Weekly", "Bi-weekly", "As needed"
    time_commitment_hours_per_week = db.Column(db.Integer)
    
    # Technology Platform
    platform_used = db.Column(db.String(100))  # Zoom, Microsoft Teams, Canvas, etc.
    platform_url = db.Column(db.String(500))
    
    # Timeline
    application_deadline = db.Column(db.Date)
    program_start_date = db.Column(db.Date)
    program_end_date = db.Column(db.Date)
    
    # Capacity
    psu_student_capacity = db.Column(db.Integer)
    partner_student_capacity = db.Column(db.Integer)
    current_psu_enrollment = db.Column(db.Integer, default=0)
    current_partner_enrollment = db.Column(db.Integer, default=0)
    
    # Requirements
    language_requirements = db.Column(db.Text)
    prerequisite_courses = db.Column(db.Text)
    gpa_requirement = db.Column(db.Numeric(3, 2))
    
    # Learning Outcomes
    learning_objectives = db.Column(db.Text)
    skills_gained = db.Column(db.Text)  # JSON array
    cultural_competencies = db.Column(db.Text)
    
    # Faculty Coordinators
    psu_faculty_coordinator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    partner_faculty_name = db.Column(db.String(200))
    partner_faculty_email = db.Column(db.String(150))
    
    # Deliverables
    final_project_required = db.Column(db.Boolean, default=False)
    presentation_required = db.Column(db.Boolean, default=False)
    research_paper_required = db.Column(db.Boolean, default=False)
    
    # Funding
    is_funded = db.Column(db.Boolean, default=False)
    funding_source = db.Column(db.String(200))
    student_cost = db.Column(db.Numeric(10, 2))
    
    # Status
    status = db.Column(db.String(30), default='active')
    # active, application_open, in_progress, completed, cancelled
    
    is_featured = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    psu_coordinator = db.relationship('User', backref='coordinated_exchange_programs')


class VirtualExchangeParticipant(db.Model):
    """Students enrolled in virtual exchange"""
    __tablename__ = 'virtual_exchange_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('virtual_exchange_programs.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Participation Details
    role = db.Column(db.String(50))  # participant, team_leader, teaching_assistant
    partner_student_paired_with = db.Column(db.String(200))  # Name of partner university student
    
    # Engagement
    sessions_attended = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer)
    attendance_rate = db.Column(db.Numeric(5, 2))
    
    # Deliverables
    final_project_submitted = db.Column(db.Boolean, default=False)
    presentation_completed = db.Column(db.Boolean, default=False)
    
    # Evaluation
    faculty_rating = db.Column(db.Integer)  # 1-5
    peer_rating = db.Column(db.Integer)
    self_reflection = db.Column(db.Text)
    
    # Outcomes
    earned_credit = db.Column(db.Boolean)
    received_certificate = db.Column(db.Boolean, default=False)
    
    # Feedback
    program_satisfaction = db.Column(db.Integer)  # 1-5
    would_recommend = db.Column(db.Boolean)
    feedback = db.Column(db.Text)
    
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    program = db.relationship('VirtualExchangeProgram', backref='participants')
    student = db.relationship('User', backref='exchange_participations')


# ==================== ADVANCED DATA & COMPLIANCE LAYER ====================

class DataAccessAudit(db.Model):
    """FERPA-compliant audit trail for all data access"""
    __tablename__ = 'data_access_audits'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Who accessed data
    accessor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    accessor_role = db.Column(db.String(50))  # student, faculty, staff, admin, system
    accessor_ip_address = db.Column(db.String(50))
    
    # What was accessed
    data_type = db.Column(db.String(100), nullable=False)
    # student_record, financial_data, health_data, grade, transcript, 
    # contact_info, emergency_contact, disciplinary_record
    
    record_id = db.Column(db.Integer)  # ID of the accessed record
    student_affected_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Whose data was accessed
    
    # How it was accessed
    access_method = db.Column(db.String(50))  # view, edit, delete, export, print, api
    endpoint = db.Column(db.String(200))  # API endpoint or page URL
    
    # Why it was accessed
    access_purpose = db.Column(db.String(100))
    # advising, registration, financial_aid, employment, research, 
    # emergency, law_enforcement, student_request, routine_maintenance
    
    justification = db.Column(db.Text)  # Optional detailed justification
    
    # Authorization
    authorization_level = db.Column(db.String(50))  # authorized, consent_given, legitimate_educational_interest
    consent_form_id = db.Column(db.Integer)  # If explicit consent was obtained
    
    # Data Details
    fields_accessed = db.Column(db.Text)  # JSON array of specific fields
    data_was_masked = db.Column(db.Boolean, default=False)
    data_was_exported = db.Column(db.Boolean, default=False)
    
    # Compliance Flags
    is_ferpa_protected = db.Column(db.Boolean, default=True)
    requires_review = db.Column(db.Boolean, default=False)
    is_suspicious = db.Column(db.Boolean, default=False)  # Flagged by AI
    
    # Audit Metadata
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_id = db.Column(db.String(100))
    user_agent = db.Column(db.String(300))
    
    # Relationships
    accessor = db.relationship('User', foreign_keys=[accessor_id], backref='data_accesses')
    student_affected = db.relationship('User', foreign_keys=[student_affected_id], backref='data_access_history')
    
    __table_args__ = (
        Index('idx_accessor_date', 'accessor_id', 'accessed_at'),
        Index('idx_student_date', 'student_affected_id', 'accessed_at'),
        Index('idx_data_type_date', 'data_type', 'accessed_at'),
    )


class ComplianceReport(db.Model):
    """Automated FERPA compliance reports"""
    __tablename__ = 'compliance_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Report Information
    report_type = db.Column(db.String(50), nullable=False)
    # annual_ferpa, quarterly_audit, incident_report, access_summary, 
    # consent_tracking, third_party_disclosure
    
    report_title = db.Column(db.String(200), nullable=False)
    report_period_start = db.Column(db.Date, nullable=False)
    report_period_end = db.Column(db.Date, nullable=False)
    
    # Report Content
    summary = db.Column(db.Text)
    total_records_reviewed = db.Column(db.Integer)
    total_access_events = db.Column(db.Integer)
    unauthorized_access_attempts = db.Column(db.Integer)
    policy_violations = db.Column(db.Integer)
    
    # Findings
    findings = db.Column(db.Text)  # JSON array of finding objects
    recommendations = db.Column(db.Text)  # JSON array
    action_items = db.Column(db.Text)  # JSON array
    
    # Compliance Status
    compliance_score = db.Column(db.Numeric(5, 2))  # 0-100
    compliant = db.Column(db.Boolean)
    issues_found = db.Column(db.Integer, default=0)
    issues_resolved = db.Column(db.Integer, default=0)
    
    # Report File
    report_file_url = db.Column(db.String(500))  # PDF or document URL
    report_format = db.Column(db.String(20))  # pdf, excel, json
    
    # Generation
    generated_by = db.Column(db.String(50))  # system_automated, admin_requested
    generated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Review
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(30), default='draft')
    # draft, under_review, approved, published, archived
    
    generator = db.relationship('User', foreign_keys=[generated_by_user_id], backref='compliance_reports_generated')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_user_id], backref='compliance_reports_reviewed')


class DataMaskingRule(db.Model):
    """Rules for real-time data masking of sensitive fields"""
    __tablename__ = 'data_masking_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rule Configuration
    rule_name = db.Column(db.String(200), nullable=False)
    data_category = db.Column(db.String(50), nullable=False)
    # financial, health, disciplinary, ssn, grades, contact_info
    
    field_name = db.Column(db.String(100), nullable=False)  # Database field name
    table_name = db.Column(db.String(100))
    
    # Masking Strategy
    masking_type = db.Column(db.String(50), nullable=False)
    # full_redaction, partial_mask, tokenization, encryption, aggregation
    
    mask_pattern = db.Column(db.String(100))  # e.g., "XXX-XX-1234" for SSN
    
    # Conditional Masking
    apply_for_roles = db.Column(db.Text)  # JSON array of roles that see masked data
    exempt_roles = db.Column(db.Text)  # JSON array of roles that see real data
    
    requires_explicit_consent = db.Column(db.Boolean, default=False)
    
    # Compliance
    ferpa_requirement = db.Column(db.Boolean, default=False)
    hipaa_requirement = db.Column(db.Boolean, default=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Audit
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', backref='masking_rules_created')
