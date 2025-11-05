"""
Seed file for all 8 new student features
Run with: python seed_student_features.py
"""

from app_pro import app
from extensions import db
from models_student_features import (
    TextbookListing, HousingListing, HousingReview, StudentDiscount,
    GradeDistribution, ProfessorReview, ProfessorProfile, CampusService,
    ServiceWaitReport, StudentEvent, EventRSVP, CourseMaterial
)
from models import User
from datetime import datetime, timedelta
from decimal import Decimal
import random

def seed_textbooks():
    """Seed textbook listings"""
    print("🎓 Seeding textbook listings...")
    
    textbooks = [
        # Psychology
        {"title": "Psychology: Themes and Variations", "author": "Wayne Weiten", "isbn": "9781305498204", 
         "edition": "10th", "course_code": "PSYCH 101", "course_name": "Introduction to Psychology",
         "condition": "Good", "price": 45.00, "original_price": 120.00, "is_negotiable": True,
         "description": "Great condition, minimal highlighting. Used for one semester."},
        
        {"title": "Abnormal Psychology", "author": "Ronald Comer", "isbn": "9781319066949",
         "edition": "10th", "course_code": "PSYCH 301", "course_name": "Abnormal Psychology",
         "condition": "Like New", "price": 65.00, "original_price": 150.00, "is_negotiable": False,
         "description": "Barely used, no markings. Comes with online access code."},
        
        # Biology
        {"title": "Campbell Biology", "author": "Jane Reece", "isbn": "9780134093413",
         "edition": "11th", "course_code": "BIOL 101", "course_name": "General Biology",
         "condition": "Good", "price": 75.00, "original_price": 200.00, "is_negotiable": True,
         "description": "Some highlighting in first 5 chapters. Otherwise excellent condition."},
        
        {"title": "Microbiology: An Introduction", "author": "Gerard Tortora", "isbn": "9780134605180",
         "edition": "13th", "course_code": "BIOL 230", "course_name": "Microbiology",
         "condition": "Fair", "price": 35.00, "original_price": 180.00, "is_negotiable": True,
         "description": "Used but functional. Cover has wear, pages are intact."},
        
        # Chemistry
        {"title": "Chemistry: The Central Science", "author": "Brown, LeMay, Bursten", "isbn": "9780134414232",
         "edition": "14th", "course_code": "CHEM 121", "course_name": "General Chemistry I",
         "condition": "Like New", "price": 85.00, "original_price": 220.00, "is_negotiable": False,
         "description": "Perfect condition! Never opened. Changed my major."},
        
        # Mathematics
        {"title": "Calculus: Early Transcendentals", "author": "James Stewart", "isbn": "9781285741550",
         "edition": "8th", "course_code": "MATH 147", "course_name": "Calculus I",
         "condition": "Good", "price": 55.00, "original_price": 180.00, "is_negotiable": True,
         "description": "Light use, no highlighting. Great for learning calculus!"},
        
        {"title": "Linear Algebra and Its Applications", "author": "David Lay", "isbn": "9780321982384",
         "edition": "5th", "course_code": "MATH 250", "course_name": "Linear Algebra",
         "condition": "Good", "price": 45.00, "original_price": 160.00, "is_negotiable": True,
         "description": "Some notes in margins. Very helpful for studying."},
        
        # English
        {"title": "The Norton Anthology of American Literature", "author": "Various", "isbn": "9780393264548",
         "edition": "9th", "course_code": "ENG 102", "course_name": "Composition II",
         "condition": "Good", "price": 30.00, "original_price": 85.00, "is_negotiable": True,
         "description": "Standard anthology, minor wear on cover."},
        
        # Business
        {"title": "Principles of Economics", "author": "N. Gregory Mankiw", "isbn": "9781305585126",
         "edition": "8th", "course_code": "ECON 201", "course_name": "Microeconomics",
         "condition": "Like New", "price": 70.00, "original_price": 195.00, "is_negotiable": False,
         "description": "Excellent condition, used for one semester."},
        
        {"title": "Financial Accounting", "author": "Walter Harrison", "isbn": "9780134486840",
         "edition": "12th", "course_code": "ACCT 201", "course_name": "Accounting I",
         "condition": "Good", "price": 60.00, "original_price": 170.00, "is_negotiable": True,
         "description": "Some highlighting, all pages intact. Great resource!"},
        
        # Computer Science
        {"title": "Introduction to Java Programming", "author": "Y. Daniel Liang", "isbn": "9780133761313",
         "edition": "11th", "course_code": "CS 101", "course_name": "Intro to Programming",
         "condition": "Like New", "price": 50.00, "original_price": 140.00, "is_negotiable": True,
         "description": "Barely used. Perfect for learning Java!"},
        
        {"title": "Data Structures and Algorithms in Java", "author": "Michael Goodrich", "isbn": "9781118771334",
         "edition": "6th", "course_code": "CS 202", "course_name": "Data Structures",
         "condition": "Good", "price": 65.00, "original_price": 165.00, "is_negotiable": True,
         "description": "Some notes, very helpful for understanding concepts."},
        
        # History
        {"title": "The American Promise", "author": "Roark et al.", "isbn": "9781319042448",
         "edition": "7th", "course_code": "HIST 201", "course_name": "US History I",
         "condition": "Good", "price": 40.00, "original_price": 110.00, "is_negotiable": True,
         "description": "Good condition, some highlighting. Great textbook!"},
        
        # Nursing
        {"title": "Fundamentals of Nursing", "author": "Patricia Potter", "isbn": "9780323327404",
         "edition": "9th", "course_code": "NURS 101", "course_name": "Nursing Fundamentals",
         "condition": "Like New", "price": 95.00, "original_price": 250.00, "is_negotiable": False,
         "description": "Excellent condition. Must-have for nursing students!"},
        
        # Physics
        {"title": "University Physics with Modern Physics", "author": "Young and Freedman", "isbn": "9780135159552",
         "edition": "15th", "course_code": "PHYS 201", "course_name": "Physics I",
         "condition": "Good", "price": 70.00, "original_price": 190.00, "is_negotiable": True,
         "description": "Some highlighting in key sections. Solutions manual included!"},
    ]
    
    # Get first user as seller (or create test users)
    user = User.query.first()
    if not user:
        print("⚠️  No users found. Please create users first.")
        return
    
    for book_data in textbooks:
        listing = TextbookListing(
            user_id=user.id,
            **book_data
        )
        db.session.add(listing)
    
    db.session.commit()
    print(f"✅ Added {len(textbooks)} textbook listings!")


def seed_housing():
    """Seed housing listings and reviews"""
    print("🏠 Seeding housing listings...")
    
    properties = [
        {
            "property_name": "Campus View Apartments",
            "address": "123 Broadway St, Pittsburg, KS 66762",
            "landlord_name": "Campus Property Management",
            "property_type": "Apartment",
            "bedrooms": 2,
            "bathrooms": 1.0,
            "rent_min": 650,
            "rent_max": 750,
            "amenities": "Parking,Laundry,WiFi,AC",
            "utilities_included": "Water,Trash",
            "distance_to_campus": 0.3
        },
        {
            "property_name": "Gorilla Heights",
            "address": "456 Crimson Ave, Pittsburg, KS 66762",
            "landlord_name": "John Smith Properties",
            "property_type": "Apartment",
            "bedrooms": 1,
            "bathrooms": 1.0,
            "rent_min": 500,
            "rent_max": 550,
            "amenities": "Parking,WiFi,Pets",
            "utilities_included": "None",
            "distance_to_campus": 0.5
        },
        {
            "property_name": "Student House on 4th Street",
            "address": "789 4th Street, Pittsburg, KS 66762",
            "landlord_name": "Private Owner",
            "property_type": "House",
            "bedrooms": 4,
            "bathrooms": 2.0,
            "rent_min": 1400,
            "rent_max": 1400,
            "amenities": "Parking,Laundry,Yard,WiFi",
            "utilities_included": "None",
            "distance_to_campus": 0.7
        },
        {
            "property_name": "The Plaza Apartments",
            "address": "1010 Plaza Dr, Pittsburg, KS 66762",
            "landlord_name": "Plaza Management LLC",
            "property_type": "Apartment",
            "bedrooms": 2,
            "bathrooms": 2.0,
            "rent_min": 800,
            "rent_max": 900,
            "amenities": "Parking,Laundry,WiFi,AC,Pool,Gym",
            "utilities_included": "Water,Trash,Internet",
            "distance_to_campus": 1.2
        },
        {
            "property_name": "Crimson Duplex",
            "address": "222 College St, Pittsburg, KS 66762",
            "landlord_name": "Local Rentals Inc",
            "property_type": "Duplex",
            "bedrooms": 3,
            "bathrooms": 1.5,
            "rent_min": 950,
            "rent_max": 950,
            "amenities": "Parking,Laundry,Yard",
            "utilities_included": "Water",
            "distance_to_campus": 0.4
        }
    ]
    
    for prop_data in properties:
        listing = HousingListing(**prop_data)
        db.session.add(listing)
    
    db.session.commit()
    print(f"✅ Added {len(properties)} housing listings!")


def seed_discounts():
    """Seed student discounts"""
    print("💰 Seeding student discounts...")
    
    discounts = [
        {
            "business_name": "Pizza Hut Pittsburg",
            "business_type": "Restaurant",
            "address": "1501 N Broadway, Pittsburg, KS 66762",
            "phone": "(620) 231-7070",
            "discount_description": "20% off with valid student ID",
            "discount_amount": "20%",
            "requirements": "Show PSU student ID",
            "is_local": True,
            "verification_required": True
        },
        {
            "business_name": "Spotify",
            "business_type": "Entertainment",
            "website": "https://spotify.com/student",
            "discount_description": "Spotify Premium Student Plan",
            "discount_amount": "$4.99/month",
            "promo_code": "STUDENT",
            "requirements": "Verify .edu email address",
            "is_online": True,
            "verification_required": True
        },
        {
            "business_name": "Apple",
            "business_type": "Retail",
            "website": "https://apple.com/us-hed/shop",
            "discount_description": "Education pricing on Mac and iPad",
            "discount_amount": "Up to $200 off",
            "requirements": "Verify student status through UNiDAYS",
            "is_online": True,
            "verification_required": True
        },
        {
            "business_name": "Jim's Diner",
            "business_type": "Restaurant",
            "address": "1912 N Broadway, Pittsburg, KS 66762",
            "discount_description": "15% off entire meal for PSU students",
            "discount_amount": "15%",
            "requirements": "Show student ID",
            "is_local": True,
            "distance_from_campus": 1.1,
            "verification_required": True
        },
        {
            "business_name": "AMC Theaters",
            "business_type": "Entertainment",
            "discount_description": "Discounted movie tickets on Thursdays",
            "discount_amount": "$5 tickets",
            "days_valid": "Thursday",
            "requirements": "Show valid student ID at box office",
            "is_local": True,
            "verification_required": True
        },
        {
            "business_name": "Amazon Prime Student",
            "business_type": "Retail",
            "website": "https://amazon.com/student",
            "discount_description": "6 months free, then 50% off Prime",
            "discount_amount": "$7.49/month after trial",
            "requirements": "Verify .edu email",
            "is_online": True,
            "verification_required": True
        },
        {
            "business_name": "The Fitness Center",
            "business_type": "Services",
            "address": "555 Gym Blvd, Pittsburg, KS 66762",
            "discount_description": "Student membership discount",
            "discount_amount": "$20/month",
            "requirements": "Show PSU ID, sign up for 6 months",
            "is_local": True,
            "distance_from_campus": 0.8,
            "verification_required": True
        },
        {
            "business_name": "Microsoft Office 365",
            "business_type": "Services",
            "website": "https://microsoft.com/education",
            "discount_description": "Free Office 365 for students",
            "discount_amount": "Free",
            "requirements": "PSU email address",
            "is_online": True,
            "verification_required": True
        },
        {
            "business_name": "Starbucks (On Campus)",
            "business_type": "Restaurant",
            "address": "Gorilla Crossing, PSU Campus",
            "discount_description": "Student discount on beverages",
            "discount_amount": "10%",
            "requirements": "Show student ID",
            "is_local": True,
            "distance_from_campus": 0.0,
            "verification_required": True
        },
        {
            "business_name": "GitHub Student Developer Pack",
            "business_type": "Services",
            "website": "https://education.github.com/pack",
            "discount_description": "Free access to developer tools worth $200k+",
            "discount_amount": "Free",
            "requirements": "Verify student status",
            "is_online": True,
            "verification_required": True
        }
    ]
    
    for discount_data in discounts:
        discount = StudentDiscount(**discount_data)
        db.session.add(discount)
    
    db.session.commit()
    print(f"✅ Added {len(discounts)} student discounts!")


def seed_grade_distributions():
    """Seed grade distribution data"""
    print("📊 Seeding grade distributions...")
    
    courses = [
        ("PSYCH 101", "Introduction to Psychology", "Psychology", "Dr. Smith"),
        ("PSYCH 101", "Introduction to Psychology", "Psychology", "Dr. Johnson"),
        ("BIOL 101", "General Biology", "Biology", "Dr. Williams"),
        ("CHEM 121", "General Chemistry I", "Chemistry", "Dr. Brown"),
        ("MATH 147", "Calculus I", "Mathematics", "Dr. Davis"),
        ("MATH 147", "Calculus I", "Mathematics", "Dr. Miller"),
        ("ENG 102", "Composition II", "English", "Dr. Wilson"),
        ("CS 101", "Intro to Programming", "Computer Science", "Dr. Moore"),
        ("HIST 201", "US History I", "History", "Dr. Taylor"),
        ("ECON 201", "Microeconomics", "Economics", "Dr. Anderson")
    ]
    
    semesters = ["Fall 2023", "Spring 2024", "Fall 2024"]
    
    for course_code, course_name, department, professor in courses:
        for semester in semesters:
            year = int(semester.split()[-1])
            
            # Generate realistic grade distribution
            total = random.randint(25, 45)
            grade_a = int(total * random.uniform(0.20, 0.35))
            grade_b = int(total * random.uniform(0.25, 0.35))
            grade_c = int(total * random.uniform(0.15, 0.25))
            grade_d = int(total * random.uniform(0.05, 0.10))
            grade_f = int(total * random.uniform(0.02, 0.08))
            grade_w = total - (grade_a + grade_b + grade_c + grade_d + grade_f)
            
            # Calculate GPA (A=4.0, B=3.0, C=2.0, D=1.0, F=0.0)
            gpa = (grade_a * 4.0 + grade_b * 3.0 + grade_c * 2.0 + grade_d * 1.0) / (total - grade_w) if total - grade_w > 0 else 0
            pass_rate = ((grade_a + grade_b + grade_c + grade_d) / total * 100) if total > 0 else 0
            
            dist = GradeDistribution(
                course_code=course_code,
                course_name=course_name,
                department=department,
                professor_name=professor,
                semester=semester.split()[0],
                year=year,
                grade_a=grade_a,
                grade_b=grade_b,
                grade_c=grade_c,
                grade_d=grade_d,
                grade_f=grade_f,
                grade_w=grade_w,
                total_students=total,
                gpa_average=round(gpa, 2),
                pass_rate=round(pass_rate, 2),
                data_source="student_reported"
            )
            db.session.add(dist)
    
    db.session.commit()
    print(f"✅ Added grade distributions for {len(courses)} courses across {len(semesters)} semesters!")


def seed_professor_reviews():
    """Seed professor reviews and profiles"""
    print("👨‍🏫 Seeding professor reviews...")
    
    professors = [
        ("Dr. Sarah Smith", "Psychology"),
        ("Dr. Michael Johnson", "Psychology"),
        ("Dr. Emily Williams", "Biology"),
        ("Dr. Robert Brown", "Chemistry"),
        ("Dr. Jennifer Davis", "Mathematics"),
        ("Dr. William Miller", "Mathematics"),
        ("Dr. Lisa Wilson", "English"),
        ("Dr. James Moore", "Computer Science"),
        ("Dr. Patricia Taylor", "History"),
        ("Dr. David Anderson", "Economics")
    ]
    
    # Create professor profiles
    for name, dept in professors:
        profile = ProfessorProfile(
            name=name,
            department=dept
        )
        db.session.add(profile)
    
    db.session.commit()
    print(f"✅ Added {len(professors)} professor profiles!")


def seed_campus_services():
    """Seed campus services for wait time tracking"""
    print("⏰ Seeding campus services...")
    
    services = [
        {
            "name": "Gibson Dining Hall",
            "category": "Dining",
            "location": "Gibson Hall, Main Campus",
            "description": "Main dining hall with all-you-can-eat buffet",
            "hours_monday": "7:00 AM - 8:00 PM",
            "hours_tuesday": "7:00 AM - 8:00 PM",
            "hours_wednesday": "7:00 AM - 8:00 PM",
            "hours_thursday": "7:00 AM - 8:00 PM",
            "hours_friday": "7:00 AM - 7:00 PM",
            "hours_saturday": "10:00 AM - 6:00 PM",
            "hours_sunday": "10:00 AM - 6:00 PM",
            "peak_hours": "12:00 PM - 1:30 PM, 5:00 PM - 6:30 PM"
        },
        {
            "name": "Gorilla Crossing",
            "category": "Dining",
            "location": "Memorial Auditorium",
            "description": "Food court with multiple vendors",
            "hours_monday": "7:00 AM - 9:00 PM",
            "hours_tuesday": "7:00 AM - 9:00 PM",
            "hours_wednesday": "7:00 AM - 9:00 PM",
            "hours_thursday": "7:00 AM - 9:00 PM",
            "hours_friday": "7:00 AM - 7:00 PM",
            "hours_saturday": "Closed",
            "hours_sunday": "Closed",
            "peak_hours": "11:30 AM - 1:00 PM"
        },
        {
            "name": "Gorilla Fitness Center",
            "category": "Gym",
            "location": "Recreation Center",
            "description": "Main campus fitness facility",
            "hours_monday": "6:00 AM - 11:00 PM",
            "hours_tuesday": "6:00 AM - 11:00 PM",
            "hours_wednesday": "6:00 AM - 11:00 PM",
            "hours_thursday": "6:00 AM - 11:00 PM",
            "hours_friday": "6:00 AM - 9:00 PM",
            "hours_saturday": "8:00 AM - 8:00 PM",
            "hours_sunday": "10:00 AM - 10:00 PM",
            "peak_hours": "4:00 PM - 7:00 PM"
        },
        {
            "name": "Axe Library",
            "category": "Library",
            "location": "Leonard H. Axe Library",
            "description": "Main campus library with study spaces",
            "hours_monday": "7:30 AM - 12:00 AM",
            "hours_tuesday": "7:30 AM - 12:00 AM",
            "hours_wednesday": "7:30 AM - 12:00 AM",
            "hours_thursday": "7:30 AM - 12:00 AM",
            "hours_friday": "7:30 AM - 6:00 PM",
            "hours_saturday": "10:00 AM - 6:00 PM",
            "hours_sunday": "12:00 PM - 12:00 AM",
            "peak_hours": "2:00 PM - 5:00 PM, 7:00 PM - 10:00 PM"
        },
        {
            "name": "Student Health Center",
            "category": "Health",
            "location": "Whitesitt Hall",
            "description": "On-campus health services",
            "hours_monday": "8:00 AM - 5:00 PM",
            "hours_tuesday": "8:00 AM - 5:00 PM",
            "hours_wednesday": "8:00 AM - 5:00 PM",
            "hours_thursday": "8:00 AM - 5:00 PM",
            "hours_friday": "8:00 AM - 5:00 PM",
            "hours_saturday": "Closed",
            "hours_sunday": "Closed",
            "peak_hours": "9:00 AM - 11:00 AM"
        },
        {
            "name": "Registrar's Office",
            "category": "Admin",
            "location": "Russ Hall, Room 101",
            "description": "Registration and records office",
            "hours_monday": "8:00 AM - 5:00 PM",
            "hours_tuesday": "8:00 AM - 5:00 PM",
            "hours_wednesday": "8:00 AM - 5:00 PM",
            "hours_thursday": "8:00 AM - 5:00 PM",
            "hours_friday": "8:00 AM - 5:00 PM",
            "hours_saturday": "Closed",
            "hours_sunday": "Closed",
            "peak_hours": "10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM"
        }
    ]
    
    for service_data in services:
        service = CampusService(**service_data)
        db.session.add(service)
    
    db.session.commit()
    print(f"✅ Added {len(services)} campus services!")


def seed_student_events():
    """Seed student events"""
    print("📅 Seeding student events...")
    
    user = User.query.first()
    if not user:
        print("⚠️  No users found. Please create users first.")
        return
    
    now = datetime.utcnow()
    
    events = [
        {
            "title": "Fall Welcome Party",
            "description": "Join us for food, games, and meeting new friends!",
            "event_type": "Social",
            "category": "Party",
            "organizer_id": user.id,
            "organization_name": "Student Activities Board",
            "start_datetime": now + timedelta(days=3, hours=18),
            "end_datetime": now + timedelta(days=3, hours=22),
            "location_name": "Student Union Ballroom",
            "is_free": True,
            "students_only": True
        },
        {
            "title": "Career Fair 2024",
            "description": "Meet with employers and explore career opportunities",
            "event_type": "Academic",
            "category": "Career",
            "organizer_id": user.id,
            "organization_name": "Career Services",
            "start_datetime": now + timedelta(days=14, hours=10),
            "end_datetime": now + timedelta(days=14, hours=16),
            "location_name": "Overman Student Center",
            "is_free": True,
            "rsvp_required": True,
            "capacity": 500
        },
        {
            "title": "Football: PSU vs. Emporia State",
            "description": "Cheer on the Gorillas!",
            "event_type": "Sports",
            "category": "Football",
            "organizer_id": user.id,
            "organization_name": "PSU Athletics",
            "start_datetime": now + timedelta(days=7, hours=14),
            "end_datetime": now + timedelta(days=7, hours=17),
            "location_name": "Carnie Smith Stadium",
            "is_free": False,
            "cost": 10.00,
            "capacity": 7000
        },
        {
            "title": "Study Group: Calculus I",
            "description": "Weekly study session for MATH 147 students",
            "event_type": "Academic",
            "category": "Study Group",
            "organizer_id": user.id,
            "organization_name": "Math Club",
            "start_datetime": now + timedelta(days=2, hours=18),
            "end_datetime": now + timedelta(days=2, hours=20),
            "location_name": "Axe Library, Room 201",
            "is_free": True,
            "is_recurring": True,
            "recurrence_pattern": "Weekly on Tuesdays"
        },
        {
            "title": "Greek Life Rush Week",
            "description": "Explore fraternity and sorority life at PSU",
            "event_type": "Greek Life",
            "category": "Recruitment",
            "organizer_id": user.id,
            "organization_name": "Interfraternity Council",
            "start_datetime": now + timedelta(days=10, hours=17),
            "end_datetime": now + timedelta(days=14, hours=21),
            "location_name": "Various Greek Houses",
            "is_free": True,
            "students_only": True
        },
        {
            "title": "Charity 5K Run",
            "description": "Run for a cause! All proceeds go to local food bank",
            "event_type": "Social",
            "category": "Fundraiser",
            "organizer_id": user.id,
            "organization_name": "Community Service Club",
            "start_datetime": now + timedelta(days=21, hours=8),
            "end_datetime": now + timedelta(days=21, hours=12),
            "location_name": "Campus Green",
            "is_free": False,
            "cost": 15.00,
            "capacity": 200
        }
    ]
    
    for event_data in events:
        event = StudentEvent(**event_data)
        db.session.add(event)
    
    db.session.commit()
    print(f"✅ Added {len(events)} student events!")


def seed_course_materials():
    """Seed course materials"""
    print("📁 Seeding course materials...")
    
    user = User.query.first()
    if not user:
        print("⚠️  No users found. Please create users first.")
        return
    
    materials = [
        {
            "course_code": "PSYCH 101",
            "course_name": "Introduction to Psychology",
            "department": "Psychology",
            "professor_name": "Dr. Smith",
            "semester": "Fall 2024",
            "title": "Chapter 1-5 Study Guide",
            "material_type": "Study Guide",
            "description": "Comprehensive study guide covering first 5 chapters. Includes key terms and practice questions.",
            "tags": "midterm,exam1,chapters1-5",
            "uploader_id": user.id
        },
        {
            "course_code": "PSYCH 101",
            "course_name": "Introduction to Psychology",
            "department": "Psychology",
            "professor_name": "Dr. Smith",
            "semester": "Fall 2024",
            "title": "Midterm Exam Study Notes",
            "material_type": "Notes",
            "description": "Detailed notes from lectures 1-10. Very helpful for midterm prep!",
            "tags": "midterm,notes,lectures",
            "uploader_id": user.id
        },
        {
            "course_code": "BIOL 101",
            "course_name": "General Biology",
            "department": "Biology",
            "professor_name": "Dr. Williams",
            "semester": "Spring 2024",
            "title": "Cell Biology Lecture Slides",
            "material_type": "Slides",
            "description": "PowerPoint slides from cell biology unit",
            "tags": "cells,biology,unit2",
            "uploader_id": user.id
        },
        {
            "course_code": "MATH 147",
            "course_name": "Calculus I",
            "department": "Mathematics",
            "professor_name": "Dr. Davis",
            "semester": "Fall 2024",
            "title": "Calculus Formulas Cheat Sheet",
            "material_type": "Study Guide",
            "description": "All important formulas and derivatives in one place",
            "tags": "formulas,derivatives,integrals",
            "uploader_id": user.id
        },
        {
            "course_code": "CS 101",
            "course_name": "Intro to Programming",
            "department": "Computer Science",
            "professor_name": "Dr. Moore",
            "semester": "Fall 2024",
            "title": "Java Basics Practice Problems",
            "material_type": "Assignment",
            "description": "50 practice problems with solutions for Java beginners",
            "tags": "java,practice,programming",
            "uploader_id": user.id
        },
        {
            "course_code": "CHEM 121",
            "course_name": "General Chemistry I",
            "department": "Chemistry",
            "professor_name": "Dr. Brown",
            "semester": "Fall 2024",
            "title": "Lab Report Template",
            "material_type": "Other",
            "description": "Standard lab report template that follows Dr. Brown's requirements",
            "tags": "lab,template,format",
            "uploader_id": user.id
        }
    ]
    
    for material_data in materials:
        material = CourseMaterial(**material_data)
        db.session.add(material)
    
    db.session.commit()
    print(f"✅ Added {len(materials)} course materials!")


def main():
    """Main seeding function"""
    print("\n" + "="*60)
    print("🌱 SEEDING ALL STUDENT FEATURES")
    print("="*60 + "\n")
    
    with app.app_context():
        try:
            seed_textbooks()
            seed_housing()
            seed_discounts()
            seed_grade_distributions()
            seed_professor_reviews()
            seed_campus_services()
            seed_student_events()
            seed_course_materials()
            
            print("\n" + "="*60)
            print("✅ ALL FEATURES SEEDED SUCCESSFULLY!")
            print("="*60)
            print("\n🎉 Your student platform is now loaded with data!")
            print("📝 You can now test all 8 new features:\n")
            print("   1. 📚 Textbook Exchange - Buy/sell textbooks")
            print("   2. 🏠 Housing Reviews - Find off-campus housing")
            print("   3. 💰 Student Discounts - Save money around town")
            print("   4. 📊 Grade Explorer - Check grade distributions")
            print("   5. 👨‍🏫 Professor Reviews - Read professor ratings")
            print("   6. ⏰ Campus Wait Times - Check service availability")
            print("   7. 📅 Student Events - Discover campus events")
            print("   8. 📁 Course Library - Share study materials")
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
