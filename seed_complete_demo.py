"""
COMPLETE DEMO DATA SEEDER FOR PRESENTATION
==========================================
This script populates EVERY feature in the app with realistic demo data
Perfect for showcasing the platform to administrators
"""

from datetime import datetime, timedelta
from random import choice, randint, sample
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app_pro import app
from extensions import db
from models import (
    User, Role, Department, Alumni, Job, Post, DailyStats, 
    Scholarship, Event, EventAttendee
)
from models_growth_features import (
    UserPoints, PointTransaction, SuccessStory, StoryReaction, StoryComment,
    Referral, DirectMessage, ForumCategory, ForumTopic, ForumPost, ForumVote,
    MentorProfile, MenteeProfile, MentorshipMatch, Recommendation,
    UserBehavior, NotificationPreference, UniversityVerification
)

print("🦍 PITTSTATE-CONNECT COMPLETE DEMO DATA SEEDER")
print("=" * 60)


def safe_commit():
    """Safely commit changes with rollback on error"""
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Error: {e}")
        return False


def clear_existing_data():
    """Clear existing data to start fresh"""
    print("\n🗑️  Clearing existing data...")
    try:
        # Delete in reverse order of dependencies
        for model in [
            ForumVote, ForumPost, ForumTopic, ForumCategory,
            StoryComment, StoryReaction, SuccessStory,
            PointTransaction, UserPoints,
            MentorshipMatch, MenteeProfile, MentorProfile,
            EventAttendee, Event,
            DirectMessage, Referral, Recommendation,
            UserBehavior, NotificationPreference,
            Job, Post, DailyStats, Scholarship,
            Alumni, UniversityVerification,
            User, Department, Role
        ]:
            db.session.query(model).delete()
        safe_commit()
        print("✅ Existing data cleared")
    except Exception as e:
        print(f"⚠️  Warning during cleanup: {e}")
        db.session.rollback()


def seed_roles():
    """Create user roles"""
    print("\n👥 Seeding roles...")
    roles = [
        Role(name="Admin", description="System administrator"),
        Role(name="Student", description="Current PSU student"),
        Role(name="Alumni", description="PSU graduate"),
        Role(name="Faculty", description="PSU faculty/staff"),
        Role(name="Employer", description="Hiring employer"),
    ]
    for role in roles:
        existing = Role.query.filter_by(name=role.name).first()
        if not existing:
            db.session.add(role)
    safe_commit()
    print(f"✅ Created {len(roles)} roles")


def seed_departments():
    """Create academic departments"""
    print("\n🏛️  Seeding departments...")
    departments = [
        "Kelce College of Business",
        "College of Technology",
        "College of Education",
        "College of Arts & Sciences",
        "School of Engineering",
        "School of Nursing",
        "Department of Computer Science",
        "Department of Psychology",
        "Department of Biology",
        "Department of Communications",
    ]
    for dept_name in departments:
        existing = Department.query.filter_by(name=dept_name).first()
        if not existing:
            db.session.add(Department(name=dept_name, description=f"PSU {dept_name}"))
    safe_commit()
    print(f"✅ Created {len(departments)} departments")


def seed_users():
    """Create diverse user profiles"""
    print("\n👤 Seeding users...")
    
    roles = {role.name: role.id for role in Role.query.all()}
    departments = Department.query.all()
    
    users_data = [
        # Admins
        ("admin", "admin@pittstate.edu", "Admin", "User", roles["Admin"], None),
        ("jdoe", "jdoe@pittstate.edu", "John", "Doe", roles["Admin"], None),
        
        # Students
        ("sarah.johnson", "sarah.j@gus.pittstate.edu", "Sarah", "Johnson", roles["Student"], "Computer Science"),
        ("mike.chen", "mike.c@gus.pittstate.edu", "Mike", "Chen", roles["Student"], "Engineering"),
        ("emily.davis", "emily.d@gus.pittstate.edu", "Emily", "Davis", roles["Student"], "Business"),
        ("alex.martinez", "alex.m@gus.pittstate.edu", "Alex", "Martinez", roles["Student"], "Nursing"),
        ("jessica.brown", "jessica.b@gus.pittstate.edu", "Jessica", "Brown", roles["Student"], "Psychology"),
        ("david.wilson", "david.w@gus.pittstate.edu", "David", "Wilson", roles["Student"], "Biology"),
        ("lauren.garcia", "lauren.g@gus.pittstate.edu", "Lauren", "Garcia", roles["Student"], "Communications"),
        ("chris.anderson", "chris.a@gus.pittstate.edu", "Chris", "Anderson", roles["Student"], "Technology"),
        
        # Alumni
        ("robert.smith", "rob.smith@gmail.com", "Robert", "Smith", roles["Alumni"], "Computer Science"),
        ("jennifer.lee", "jen.lee@yahoo.com", "Jennifer", "Lee", roles["Alumni"], "Business"),
        ("michael.taylor", "m.taylor@outlook.com", "Michael", "Taylor", roles["Alumni"], "Engineering"),
        ("amanda.white", "amanda.w@gmail.com", "Amanda", "White", roles["Alumni"], "Psychology"),
        
        # Faculty
        ("dr.thompson", "thompson@pittstate.edu", "Dr. James", "Thompson", roles["Faculty"], None),
        ("prof.rodriguez", "rodriguez@pittstate.edu", "Prof. Maria", "Rodriguez", roles["Faculty"], None),
        
        # Employers
        ("hr.techcorp", "hiring@techcorp.com", "Tech Corp", "Recruiter", roles["Employer"], None),
        ("hr.innovation", "hr@innovationllc.com", "Innovation LLC", "Hiring Manager", roles["Employer"], None),
    ]
    
    for username, email, fname, lname, role_id, major in users_data:
        existing = User.query.filter_by(username=username).first()
        if not existing:
            user = User(
                username=username,
                email=email,
                first_name=fname,
                last_name=lname,
                role_id=role_id,
                major=major,
                is_active=True,
                email_confirmed=True,
                created_at=datetime.utcnow() - timedelta(days=randint(30, 365))
            )
            user.set_password("demo123")  # All demo users use password: demo123
            db.session.add(user)
    
    safe_commit()
    print(f"✅ Created {len(users_data)} users (password: demo123)")


def seed_jobs():
    """Create job postings"""
    print("\n💼 Seeding job postings...")
    
    employers = User.query.filter_by(role_id=Role.query.filter_by(name="Employer").first().id).all()
    
    jobs_data = [
        ("Software Engineer", "Tech Corp", "Full-time software development position", "Pittsburg, KS", 65000, 85000),
        ("Data Analyst", "Innovation LLC", "Analyze and visualize business data", "Remote", 55000, 70000),
        ("Marketing Coordinator", "Tech Corp", "Plan and execute marketing campaigns", "Kansas City, MO", 45000, 60000),
        ("Project Manager", "Innovation LLC", "Lead cross-functional project teams", "Joplin, MO", 70000, 90000),
        ("UX Designer", "Tech Corp", "Design user-friendly interfaces", "Remote", 60000, 80000),
        ("Sales Representative", "Innovation LLC", "Build client relationships and close deals", "Pittsburg, KS", 40000, 55000),
        ("Network Administrator", "Tech Corp", "Maintain and secure company networks", "Springfield, MO", 55000, 75000),
        ("HR Specialist", "Innovation LLC", "Recruit and onboard new employees", "Pittsburg, KS", 45000, 60000),
    ]
    
    for title, company, desc, location, min_sal, max_sal in jobs_data:
        employer = choice(employers)
        job = Job(
            title=title,
            company=company,
            description=desc,
            location=location,
            salary_min=min_sal,
            salary_max=max_sal,
            posted_by_id=employer.id,
            is_active=True,
            posted_at=datetime.utcnow() - timedelta(days=randint(1, 30))
        )
        db.session.add(job)
    
    safe_commit()
    print(f"✅ Created {len(jobs_data)} job postings")


def seed_events():
    """Create campus events"""
    print("\n📅 Seeding events...")
    
    events_data = [
        ("Career Fair 2025", "Annual career fair with 50+ employers", datetime.utcnow() + timedelta(days=15)),
        ("Tech Talk: AI in Industry", "Guest speaker from Google discusses AI applications", datetime.utcnow() + timedelta(days=7)),
        ("Alumni Networking Night", "Connect with successful PSU alumni", datetime.utcnow() + timedelta(days=21)),
        ("Resume Workshop", "Learn to build a winning resume", datetime.utcnow() + timedelta(days=3)),
        ("Hackathon 2025", "24-hour coding competition with prizes", datetime.utcnow() + timedelta(days=30)),
        ("Graduate School Fair", "Explore graduate program options", datetime.utcnow() + timedelta(days=10)),
        ("Mock Interview Day", "Practice interviews with professionals", datetime.utcnow() + timedelta(days=5)),
        ("Entrepreneurship Summit", "Learn from successful startup founders", datetime.utcnow() + timedelta(days=45)),
    ]
    
    for title, desc, date in events_data:
        event = Event(
            title=title,
            description=desc,
            event_date=date,
            location="PSU Student Union",
            max_attendees=randint(50, 200),
            created_at=datetime.utcnow() - timedelta(days=randint(1, 14))
        )
        db.session.add(event)
    
    safe_commit()
    print(f"✅ Created {len(events_data)} events")


def seed_scholarships():
    """Create scholarship opportunities"""
    print("\n🎓 Seeding scholarships...")
    
    scholarships_data = [
        ("Gorilla Excellence Scholarship", 5000, "For outstanding academic achievement", "2025-12-31"),
        ("STEM Leadership Award", 3000, "For students in STEM fields", "2025-11-30"),
        ("Community Service Grant", 2000, "For students with volunteer experience", "2026-01-15"),
        ("First Generation Scholarship", 4000, "For first-generation college students", "2025-12-15"),
        ("Athletics Scholarship", 6000, "For student athletes", "2026-02-01"),
    ]
    
    for name, amount, desc, deadline in scholarships_data:
        scholarship = Scholarship(
            name=name,
            amount=amount,
            description=desc,
            deadline=datetime.strptime(deadline, "%Y-%m-%d").date(),
            requirements="Minimum 3.0 GPA required",
            is_active=True
        )
        db.session.add(scholarship)
    
    safe_commit()
    print(f"✅ Created {len(scholarships_data)} scholarships")


def seed_success_stories():
    """Create alumni success stories"""
    print("\n🌟 Seeding success stories...")
    
    alumni = User.query.filter_by(role_id=Role.query.filter_by(name="Alumni").first().id).all()
    
    stories_data = [
        ("From PSU to Silicon Valley", "After graduating with a CS degree, I landed my dream job at Google. PSU prepared me incredibly well for the tech industry!"),
        ("Starting My Own Business", "I used skills from my business classes to launch my startup. We just secured Series A funding!"),
        ("Making a Difference in Healthcare", "As a PSU nursing grad, I'm now working at a top hospital and loving every minute of making a difference."),
        ("Career Change Success", "PSU helped me pivot from engineering to data science. Best decision I ever made!"),
    ]
    
    for i, (title, content) in enumerate(stories_data):
        if i < len(alumni):
            story = SuccessStory(
                user_id=alumni[i].id,
                title=title,
                content=content,
                graduation_year=randint(2018, 2023),
                current_position=choice(["Software Engineer", "Business Owner", "Nurse Practitioner", "Data Scientist"]),
                current_company=choice(["Google", "Own Business", "Regional Hospital", "Tech Startup"]),
                is_featured=i < 2,
                created_at=datetime.utcnow() - timedelta(days=randint(1, 90))
            )
            db.session.add(story)
    
    safe_commit()
    print(f"✅ Created {len(stories_data)} success stories")


def seed_forum():
    """Create forum categories and discussions"""
    print("\n💬 Seeding forum...")
    
    # Categories
    categories = [
        ForumCategory(name="General", description="General discussions", slug="general"),
        ForumCategory(name="Career Advice", description="Get career guidance", slug="career-advice"),
        ForumCategory(name="Student Life", description="Campus life discussions", slug="student-life"),
        ForumCategory(name="Technology", description="Tech topics", slug="technology"),
    ]
    for cat in categories:
        db.session.add(cat)
    safe_commit()
    
    students = User.query.filter_by(role_id=Role.query.filter_by(name="Student").first().id).limit(5).all()
    
    # Topics
    topics_data = [
        ("Best study spots on campus?", "general", "Looking for quiet places to study between classes. Any recommendations?"),
        ("Internship tips", "career-advice", "I'm applying for summer internships. What should I know?"),
        ("Tech stack for CS majors", "technology", "What programming languages should I focus on in 2025?"),
        ("Campus parking situation", "student-life", "Anyone else struggling with parking this semester?"),
    ]
    
    for title, cat_slug, content in topics_data:
        category = ForumCategory.query.filter_by(slug=cat_slug).first()
        author = choice(students)
        topic = ForumTopic(
            title=title,
            category_id=category.id,
            author_id=author.id,
            created_at=datetime.utcnow() - timedelta(days=randint(1, 30))
        )
        db.session.add(topic)
        safe_commit()
        
        # Add initial post
        post = ForumPost(
            topic_id=topic.id,
            author_id=author.id,
            content=content,
            created_at=topic.created_at
        )
        db.session.add(post)
        
        # Add some replies
        for _ in range(randint(2, 5)):
            replier = choice(students)
            reply = ForumPost(
                topic_id=topic.id,
                author_id=replier.id,
                content=f"Great question! Here's my take on this...",
                created_at=topic.created_at + timedelta(hours=randint(1, 48))
            )
            db.session.add(reply)
    
    safe_commit()
    print(f"✅ Created {len(categories)} forum categories with discussions")


def seed_mentorship():
    """Create mentorship connections"""
    print("\n🤝 Seeding mentorship...")
    
    students = User.query.filter_by(role_id=Role.query.filter_by(name="Student").first().id).limit(4).all()
    alumni = User.query.filter_by(role_id=Role.query.filter_by(name="Alumni").first().id).all()
    
    # Create mentor profiles
    for alum in alumni:
        profile = MentorProfile(
            user_id=alum.id,
            expertise_areas="Software Development, Career Planning",
            years_experience=randint(5, 15),
            bio=f"PSU alum passionate about helping students succeed!",
            is_active=True
        )
        db.session.add(profile)
    safe_commit()
    
    # Create mentee profiles
    for student in students:
        profile = MenteeProfile(
            user_id=student.id,
            goals="Career development, Industry insights",
            interests="Technology, Networking",
            looking_for="Experienced professional in tech industry"
        )
        db.session.add(profile)
    safe_commit()
    
    # Create matches
    for student in students:
        mentor = choice(alumni)
        match = MentorshipMatch(
            mentor_id=MentorProfile.query.filter_by(user_id=mentor.id).first().id,
            mentee_id=MenteeProfile.query.filter_by(user_id=student.id).first().id,
            status="active",
            matched_at=datetime.utcnow() - timedelta(days=randint(1, 60))
        )
        db.session.add(match)
    
    safe_commit()
    print(f"✅ Created mentorship connections")


def seed_gamification():
    """Add points and achievements"""
    print("\n🎮 Seeding gamification...")
    
    students = User.query.filter_by(role_id=Role.query.filter_by(name="Student").first().id).all()
    
    for student in students:
        # Create user points
        points = UserPoints(
            user_id=student.id,
            total_points=randint(100, 500),
            level=randint(1, 5)
        )
        db.session.add(points)
        safe_commit()
        
        # Add some point transactions
        activities = ["profile_complete", "resume_uploaded", "event_attended", "forum_post", "job_applied"]
        for _ in range(randint(3, 8)):
            transaction = PointTransaction(
                user_id=student.id,
                points=randint(10, 50),
                reason=choice(activities),
                created_at=datetime.utcnow() - timedelta(days=randint(1, 60))
            )
            db.session.add(transaction)
    
    safe_commit()
    print(f"✅ Created gamification data")


def seed_analytics():
    """Generate analytics data"""
    print("\n📊 Seeding analytics...")
    
    for i in range(30):
        date = datetime.utcnow().date() - timedelta(days=i)
        stats = DailyStats(
            date=date,
            active_users=randint(50, 150),
            new_signups=randint(2, 10),
            jobs_posted=randint(1, 5),
            applications_submitted=randint(10, 30)
        )
        db.session.add(stats)
    
    safe_commit()
    print(f"✅ Created 30 days of analytics data")


def main():
    """Run all seed functions"""
    with app.app_context():
        print("\n⚠️  WARNING: This will clear ALL existing data!")
        response = input("Continue? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
        
        clear_existing_data()
        seed_roles()
        seed_departments()
        seed_users()
        seed_jobs()
        seed_events()
        seed_scholarships()
        seed_success_stories()
        seed_forum()
        seed_mentorship()
        seed_gamification()
        seed_analytics()
        
        print("\n" + "=" * 60)
        print("🎉 DEMO DATA SEEDING COMPLETE!")
        print("=" * 60)
        print("\n📝 Login Credentials:")
        print("   Admin: admin / demo123")
        print("   Student: sarah.johnson / demo123")
        print("   Alumni: robert.smith / demo123")
        print("   Employer: hr.techcorp / demo123")
        print("\n🚀 Your app is ready for the presentation!")


if __name__ == "__main__":
    main()
