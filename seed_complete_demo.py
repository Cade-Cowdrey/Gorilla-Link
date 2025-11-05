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
        # Admins - Simple usernames
        ("admin", "admin@pittstate.edu", "System", "Administrator", roles["Admin"], None),
        ("admin2", "admin2@pittstate.edu", "John", "Doe", roles["Admin"], None),
        
        # Students - Simple username + more students
        ("student", "student@gus.pittstate.edu", "Sarah", "Johnson", roles["Student"], "Computer Science"),
        ("student2", "student2@gus.pittstate.edu", "Mike", "Chen", roles["Student"], "Engineering"),
        ("student3", "student3@gus.pittstate.edu", "Emily", "Davis", roles["Student"], "Business"),
        ("student4", "student4@gus.pittstate.edu", "Alex", "Martinez", roles["Student"], "Nursing"),
        ("student5", "student5@gus.pittstate.edu", "Jessica", "Brown", roles["Student"], "Psychology"),
        ("student6", "student6@gus.pittstate.edu", "David", "Wilson", roles["Student"], "Biology"),
        ("student7", "student7@gus.pittstate.edu", "Lauren", "Garcia", roles["Student"], "Communications"),
        ("student8", "student8@gus.pittstate.edu", "Chris", "Anderson", roles["Student"], "Technology"),
        ("student9", "student9@gus.pittstate.edu", "Rachel", "Kim", roles["Student"], "Computer Science"),
        ("student10", "student10@gus.pittstate.edu", "Brandon", "Lee", roles["Student"], "Engineering"),
        ("student11", "student11@gus.pittstate.edu", "Ashley", "Taylor", roles["Student"], "Business"),
        ("student12", "student12@gus.pittstate.edu", "Tyler", "Moore", roles["Student"], "Psychology"),
        ("student13", "student13@gus.pittstate.edu", "Madison", "White", roles["Student"], "Biology"),
        ("student14", "student14@gus.pittstate.edu", "Jordan", "Harris", roles["Student"], "Nursing"),
        ("student15", "student15@gus.pittstate.edu", "Samantha", "Clark", roles["Student"], "Communications"),
        
        # Alumni - Simple username + more alumni
        ("alumni", "alumni@gmail.com", "Robert", "Smith", roles["Alumni"], "Computer Science"),
        ("alumni2", "alumni2@yahoo.com", "Jennifer", "Lee", roles["Alumni"], "Business"),
        ("alumni3", "alumni3@outlook.com", "Michael", "Taylor", roles["Alumni"], "Engineering"),
        ("alumni4", "alumni4@gmail.com", "Amanda", "White", roles["Alumni"], "Psychology"),
        ("alumni5", "alumni5@hotmail.com", "Kevin", "Brown", roles["Alumni"], "Computer Science"),
        ("alumni6", "alumni6@gmail.com", "Lisa", "Garcia", roles["Alumni"], "Business"),
        ("alumni7", "alumni7@yahoo.com", "Daniel", "Martinez", roles["Alumni"], "Engineering"),
        ("alumni8", "alumni8@outlook.com", "Nicole", "Robinson", roles["Alumni"], "Nursing"),
        
        # Faculty - Simple username + more faculty
        ("faculty", "faculty@pittstate.edu", "Dr. James", "Thompson", roles["Faculty"], None),
        ("faculty2", "faculty2@pittstate.edu", "Prof. Maria", "Rodriguez", roles["Faculty"], None),
        ("faculty3", "faculty3@pittstate.edu", "Dr. Susan", "Miller", roles["Faculty"], None),
        ("faculty4", "faculty4@pittstate.edu", "Prof. David", "Anderson", roles["Faculty"], None),
        
        # Employers - Simple username + more employers
        ("employer", "employer@techcorp.com", "Tech Corp", "Recruiter", roles["Employer"], None),
        ("employer2", "employer2@innovationllc.com", "Innovation LLC", "Hiring Manager", roles["Employer"], None),
        ("employer3", "employer3@globaltech.com", "Global Tech", "HR Director", roles["Employer"], None),
        ("employer4", "employer4@startupxyz.com", "Startup XYZ", "Talent Scout", roles["Employer"], None),
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
        # Tech/CS Jobs (15)
        ("Software Engineer", "Tech Corp", "Kansas City, MO",
         "Join our team developing cutting-edge web applications. Requirements: BS in CS, 2+ years experience with Python/JavaScript, React/Node.js. Competitive salary and benefits."),
        ("Full Stack Developer", "Global Tech Solutions", "Remote",
         "Build scalable applications using React and Node.js. Requirements: 3+ years experience, portfolio required. Work with modern tech stack."),
        ("Mobile App Developer", "Startup XYZ", "Kansas City, MO",
         "Create iOS/Android apps. Requirements: Swift or Kotlin experience, published apps preferred. Fast-paced startup environment."),
        ("DevOps Engineer", "Tech Corp", "Wichita, KS",
         "Manage cloud infrastructure and CI/CD pipelines. Requirements: AWS/Azure experience, Docker/Kubernetes, Terraform. $80k-$95k."),
        ("Cybersecurity Analyst", "Global Tech Solutions", "Kansas City, MO",
         "Protect systems from threats. Requirements: Security+, CEH, or CISSP certification preferred. Penetration testing experience."),
        ("QA Engineer", "Tech Corp", "Remote",
         "Test software and ensure quality. Requirements: Experience with automated testing, Selenium/Jest, CI/CD pipelines. $65k-$80k."),
        ("Systems Administrator", "Innovation LLC", "Pittsburg, KS",
         "Maintain IT infrastructure. Requirements: Windows/Linux administration, networking knowledge, Active Directory. Great benefits."),
        ("Web Developer Intern", "Tech Corp", "Remote",
         "Summer internship building modern web applications. Requirements: CS student, HTML/CSS/JavaScript knowledge. Paid internship $20/hr."),
        ("Backend Developer", "Global Tech Solutions", "Remote",
         "Build APIs and microservices. Requirements: Python/Java, REST APIs, database design. Docker experience preferred. $75k-$90k."),
        ("Frontend Developer", "Startup XYZ", "Kansas City, MO",
         "Create beautiful user interfaces. Requirements: React/Vue.js, responsive design, TypeScript. Portfolio required. $65k-$85k."),
        ("Cloud Architect", "Global Tech Solutions", "Remote",
         "Design cloud solutions. Requirements: AWS/Azure certified, 5+ years experience, infrastructure as code. $95k-$120k."),
        ("Database Administrator", "Tech Corp", "Pittsburg, KS",
         "Manage production databases. Requirements: SQL Server/PostgreSQL, performance tuning, backup/recovery. $70k-$85k."),
        ("UI/UX Designer", "Startup XYZ", "Remote",
         "Design user experiences for web/mobile. Requirements: Figma/Sketch, user research experience, design system knowledge. Portfolio required."),
        ("Software Development Intern", "Innovation LLC", "Wichita, KS",
         "Summer internship for CS students. Requirements: Currently enrolled, basic programming knowledge, Git. Paid $18-$22/hr."),
        ("Machine Learning Engineer", "Global Tech Solutions", "Kansas City, MO",
         "Build AI/ML models. Requirements: Python, TensorFlow/PyTorch, statistics background. MS/PhD preferred. $90k-$110k."),
        
        # Business/Analytics Jobs (12)
        ("Data Analyst", "Innovation LLC", "Wichita, KS",
         "Analyze business data and create insights. Requirements: Strong SQL skills, experience with Tableau or Power BI. Statistics background. $65k-$75k."),
        ("Business Analyst", "Tech Corp", "Kansas City, MO",
         "Bridge gap between business and IT. Requirements: Business degree, analytical mindset, requirements gathering. $60k-$75k."),
        ("Financial Analyst", "Global Tech Solutions", "Kansas City, MO",
         "Analyze financial data and create reports. Requirements: Finance degree, Excel expertise, CFA preferred. Financial modeling. $68k-$82k."),
        ("Marketing Coordinator", "Tech Corp", "Remote",
         "Support marketing campaigns and social media. Requirements: Marketing degree, excellent communication skills. SEO/SEM knowledge. $50k-$60k."),
        ("Digital Marketing Specialist", "Startup XYZ", "Remote",
         "Manage digital campaigns, SEO, and analytics. Requirements: Google Analytics, AdWords experience. Content creation skills. $55k-$68k."),
        ("Sales Representative", "Innovation LLC", "Wichita, KS",
         "B2B sales role with commission. Requirements: Sales experience, excellent communication skills. CRM knowledge. Base $52k + commission."),
        ("Project Manager", "Global Tech Solutions", "Kansas City, MO",
         "Lead cross-functional projects. Requirements: PMP certification preferred, 3+ years PM experience. Agile/Scrum. $72k-$90k."),
        ("HR Coordinator", "Tech Corp", "Kansas City, MO",
         "Support recruitment and employee relations. Requirements: HR degree, SHRM-CP preferred. ATS experience. $48k-$58k."),
        ("Business Intelligence Analyst", "Global Tech Solutions", "Remote",
         "Create data dashboards and reports. Requirements: SQL, Power BI/Tableau, data warehousing. ETL experience. $70k-$85k."),
        ("Marketing Intern", "Startup XYZ", "Wichita, KS",
         "Assist with marketing campaigns. Requirements: Marketing major, creative mindset, social media savvy. Paid $18/hr."),
        ("Account Manager", "Innovation LLC", "Kansas City, MO",
         "Manage client relationships. Requirements: Customer service experience, communication skills. Account management software. $58k-$70k."),
        ("Operations Manager", "Tech Corp", "Pittsburg, KS",
         "Oversee daily operations. Requirements: Operations experience, process improvement, team leadership. $65k-$80k."),
        
        # Engineering Jobs (8)
        ("Mechanical Engineer", "Innovation Manufacturing", "Wichita, KS",
         "Design mechanical systems. Requirements: BSME, SolidWorks experience, PE license preferred. HVAC or automotive. $70k-$85k."),
        ("Electrical Engineer", "Global Tech Solutions", "Kansas City, MO",
         "Design electrical systems and circuits. Requirements: BSEE, 2+ years experience. PCB design, power systems. $72k-$88k."),
        ("Civil Engineer", "KC Engineering Firm", "Kansas City, MO",
         "Infrastructure design and planning. Requirements: BSCE, AutoCAD, PE license preferred. Transportation projects. $65k-$82k."),
        ("Junior Engineer", "Innovation Manufacturing", "Joplin, MO",
         "Entry-level engineering position. Requirements: Engineering degree, CAD experience preferred. Mechanical or electrical. $55k-$65k."),
        ("Chemical Engineer", "Regional Chemical Co", "Pittsburg, KS",
         "Process engineering and optimization. Requirements: BSChE, 2+ years experience. Safety certifications. $68k-$85k."),
        ("Manufacturing Engineer", "Innovation Manufacturing", "Joplin, MO",
         "Improve production processes. Requirements: Engineering degree, lean manufacturing, Six Sigma. AutoCAD. $65k-$80k."),
        ("Engineering Intern", "KC Engineering Firm", "Kansas City, MO",
         "Hands-on engineering experience. Requirements: Engineering major, CAD skills, team player. Summer position $22/hr."),
        ("Quality Engineer", "Innovation Manufacturing", "Wichita, KS",
         "Ensure product quality. Requirements: Engineering degree, quality systems, ISO standards. Root cause analysis. $62k-$75k."),
        
        # Healthcare Jobs (6)
        ("Registered Nurse", "Community Hospital", "Pittsburg, KS",
         "Provide patient care in medical-surgical unit. Requirements: BSN, Kansas RN license, ACLS certification. Excellent benefits."),
        ("Nurse Practitioner", "Regional Medical Center", "Joplin, MO",
         "Primary care provider role. Requirements: MSN, NP certification, prescriptive authority. Family practice. $95k-$115k."),
        ("Physical Therapist", "Community Hospital", "Pittsburg, KS",
         "Provide rehabilitation services. Requirements: DPT degree, state license. Outpatient orthopedics. $70k-$85k."),
        ("Medical Lab Technologist", "Regional Medical Center", "Joplin, MO",
         "Perform laboratory tests. Requirements: BS in Medical Technology, ASCP certification. Hospital lab experience. $58k-$68k."),
        ("Pharmacy Technician", "Community Hospital", "Pittsburg, KS",
         "Assist pharmacists with medications. Requirements: Pharmacy tech certification, hospital experience preferred. $38k-$45k."),
        ("Healthcare Administrator", "Regional Medical Center", "Joplin, MO",
         "Manage healthcare operations. Requirements: Healthcare administration degree, 3+ years experience. Budget management. $75k-$92k."),
        
        # Education Jobs (4)
        ("Academic Advisor", "Pittsburg State University", "Pittsburg, KS",
         "Guide students on academic matters. Requirements: Master's degree, student services experience. Knowledge of degree programs."),
        ("Instructional Designer", "Online Education Inc", "Remote",
         "Create online course content. Requirements: Education degree, LMS experience, instructional design. Articulate/Canvas. $58k-$70k."),
        ("Career Counselor", "Community College", "Joplin, MO",
         "Help students with career planning. Requirements: Counseling degree, career assessment tools. Resume/interview coaching. $52k-$62k."),
        ("Training Coordinator", "Tech Corp", "Kansas City, MO",
         "Develop employee training programs. Requirements: Training experience, presentation skills, LMS administration. $55k-$68k."),
        
        # Creative/Design Jobs (5)
        ("Graphic Designer", "Creative Agency KC", "Kansas City, MO",
         "Create visual content for marketing. Requirements: Adobe Creative Suite, portfolio required. Print and digital design. $52k-$65k."),
        ("Content Writer", "Tech Corp", "Remote",
         "Create technical documentation and blog posts. Requirements: Excellent writing skills, tech background helpful. SEO knowledge. $48k-$60k."),
        ("Video Editor", "Media Production Co", "Kansas City, MO",
         "Edit video content. Requirements: Adobe Premiere/After Effects, portfolio. Motion graphics experience. $50k-$65k."),
        ("Social Media Manager", "Startup XYZ", "Remote",
         "Manage company social media presence. Requirements: Social media experience, content creation skills. Analytics. $50k-$62k."),
        ("Brand Designer", "Creative Agency KC", "Kansas City, MO",
         "Develop brand identities. Requirements: Graphic design degree, portfolio, typography skills. Branding projects. $58k-$72k."),
    ]
    
    for title, company, location, desc in jobs_data:
        employer = choice(employers) if employers else None
        job = Job(
            title=title,
            company=company,
            description=desc,
            location=location,
            posted_at=datetime.utcnow() - timedelta(days=randint(1, 30)),
            is_active=True
        )
        db.session.add(job)
    
    safe_commit()
    print(f"✅ Created {len(jobs_data)} job postings")


def seed_events():
    """Create campus events"""
    print("\n📅 Seeding events...")
    
    events_data = [
        # Career & Professional Development (12)
        ("Spring Career Fair 2025", "Annual career fair with 50+ employers from tech, healthcare, business, and engineering sectors. Bring resumes!", 
         datetime.utcnow() + timedelta(days=15), "PSU Student Center Ballroom", 300),
        ("Tech Talk: AI in Industry", "Guest speaker from Google discusses real-world AI applications and career opportunities in machine learning",
         datetime.utcnow() + timedelta(days=7), "Technology Center Auditorium", 150),
        ("Resume & Cover Letter Workshop", "Learn to build a winning resume and cover letter from career services professionals. Bring laptop!",
         datetime.utcnow() + timedelta(days=3), "Career Services Office", 40),
        ("Mock Interview Day", "Practice interviews with industry professionals. Schedule your 30-minute session in advance.",
         datetime.utcnow() + timedelta(days=5), "Business Building Room 205", 60),
        ("Graduate School Fair", "Explore graduate program options from universities across the region. Meet admissions counselors.",
         datetime.utcnow() + timedelta(days=10), "PSU Student Union", 200),
        ("LinkedIn Profile Workshop", "Optimize your LinkedIn profile to attract recruiters and make professional connections",
         datetime.utcnow() + timedelta(days=12), "Library Computer Lab", 30),
        ("Salary Negotiation Workshop", "Learn negotiation strategies to maximize your job offer. Real examples and role-play scenarios.",
         datetime.utcnow() + timedelta(days=18), "Career Services Office", 40),
        ("Industry Panel: Healthcare Careers", "Panel of healthcare professionals discuss career paths in nursing, allied health, and administration",
         datetime.utcnow() + timedelta(days=20), "Nursing Building Auditorium", 100),
        ("Tech Industry Recruiting Event", "Meet recruiters from Google, Microsoft, Amazon, and local tech companies",
         datetime.utcnow() + timedelta(days=25), "Technology Center", 200),
        ("Entrepreneurship Panel", "Successful PSU alumni entrepreneurs share their startup journeys and lessons learned",
         datetime.utcnow() + timedelta(days=28), "Business Building Auditorium", 120),
        ("Summer Internship Fair", "Find your summer internship! Companies seeking interns in all majors.",
         datetime.utcnow() + timedelta(days=35), "PSU Student Center", 250),
        ("Professional Etiquette Dinner", "Learn business dining etiquette while networking. Business attire required. Free dinner!",
         datetime.utcnow() + timedelta(days=40), "University Dining Hall", 60),
        
        # Networking Events (8)
        ("Alumni Networking Night", "Connect with successful PSU alumni from diverse industries. Heavy appetizers and drinks provided.",
         datetime.utcnow() + timedelta(days=21), "Alumni Center", 150),
        ("Speed Networking Event", "Meet 20+ professionals in rapid 3-minute sessions. Great way to expand your network!",
         datetime.utcnow() + timedelta(days=14), "Student Union Ballroom", 100),
        ("Women in STEM Mixer", "Networking event for women in science, technology, engineering, and math fields",
         datetime.utcnow() + timedelta(days=17), "Technology Center Lounge", 80),
        ("Business Professionals Breakfast", "Early morning networking with local business leaders. Continental breakfast provided.",
         datetime.utcnow() + timedelta(days=23), "Business Building Atrium", 50),
        ("Engineering Industry Meetup", "Network with engineers from manufacturing, construction, and tech companies",
         datetime.utcnow() + timedelta(days=26), "Engineering Building", 90),
        ("Healthcare Networking Social", "Connect with healthcare professionals from hospitals, clinics, and health systems",
         datetime.utcnow() + timedelta(days=32), "Nursing Building", 70),
        ("Young Professionals Mixer", "Network with recent PSU grads (graduated within 5 years). Share experiences and advice.",
         datetime.utcnow() + timedelta(days=38), "Downtown Pittsburg Venue", 100),
        ("Industry Leaders Lunch", "Exclusive lunch with C-level executives from regional companies. Application required.",
         datetime.utcnow() + timedelta(days=42), "University Club", 25),
        
        # Tech & Innovation (6)
        ("Hackathon 2025", "24-hour coding competition with prizes! Form teams, build cool projects, win cash and swag.",
         datetime.utcnow() + timedelta(days=30), "Technology Center - 24hr access", 150),
        ("Web Development Bootcamp", "Intensive 2-day workshop: HTML, CSS, JavaScript, React basics. Bring laptop!",
         datetime.utcnow() + timedelta(days=8), "Computer Lab 301", 40),
        ("Mobile App Development Workshop", "Learn to build iOS and Android apps. iOS: Swift, Android: Kotlin",
         datetime.utcnow() + timedelta(days=16), "Technology Center Lab", 35),
        ("Cybersecurity Workshop", "Hands-on ethical hacking and security testing. Learn penetration testing basics.",
         datetime.utcnow() + timedelta(days=24), "Computer Lab 405", 30),
        ("Data Science Symposium", "Presentations on machine learning, data visualization, and analytics from students and faculty",
         datetime.utcnow() + timedelta(days=33), "Science Building Auditorium", 100),
        ("Tech Startup Pitch Competition", "Student entrepreneurs pitch their startup ideas. $5000 grand prize!",
         datetime.utcnow() + timedelta(days=45), "Business Building Auditorium", 200),
        
        # Student Life & Campus (8)
        ("Welcome Week Kickoff", "Start the semester with campus tours, free food, games, and student org fair!",
         datetime.utcnow() + timedelta(days=2), "Central Quad", 500),
        ("Student Organization Fair", "Explore 100+ student clubs and organizations. Find your community!",
         datetime.utcnow() + timedelta(days=4), "Student Union - All Floors", 400),
        ("Homecoming Week Events", "Pep rally, parade, tailgate, football game, and alumni reunion activities all week!",
         datetime.utcnow() + timedelta(days=27), "Various Campus Locations", 2000),
        ("Spring Concert Series", "Live music every Friday evening on the quad. Local and student bands.",
         datetime.utcnow() + timedelta(days=11), "Central Quad", 300),
        ("International Food Festival", "Sample cuisines from around the world. Hosted by International Student Association.",
         datetime.utcnow() + timedelta(days=19), "Student Union Ballroom", 250),
        ("Mental Health Awareness Week", "Workshops, resources, and activities promoting student mental wellness",
         datetime.utcnow() + timedelta(days=22), "Various Campus Locations", 200),
        ("Study Abroad Fair", "Learn about study abroad opportunities in 30+ countries. Meet program coordinators.",
         datetime.utcnow() + timedelta(days=29), "International Programs Office", 100),
        ("End of Year Celebration", "Celebrate the semester's end! Food, games, prizes, and live entertainment.",
         datetime.utcnow() + timedelta(days=60), "Central Quad", 800),
        
        # Academic & Learning (6)
        ("Research Symposium", "Undergraduate and graduate students present their research. All disciplines welcome!",
         datetime.utcnow() + timedelta(days=36), "Library Conference Center", 150),
        ("Graduate School Application Workshop", "Step-by-step guide to applying to graduate programs. GRE prep tips included.",
         datetime.utcnow() + timedelta(days=13), "Career Services Office", 50),
        ("Time Management Workshop", "Learn proven techniques to balance academics, work, and personal life",
         datetime.utcnow() + timedelta(days=6), "Student Success Center", 40),
        ("Academic Success Bootcamp", "Study skills, note-taking, test prep strategies. For all students!",
         datetime.utcnow() + timedelta(days=9), "Library Learning Commons", 60),
        ("Writing Center Open House", "Tour the Writing Center, meet tutors, learn about free tutoring services",
         datetime.utcnow() + timedelta(days=31), "Writing Center - Library 2nd Floor", 30),
        ("Honors Program Information Session", "Learn about joining the Honors Program. Benefits, requirements, application process.",
         datetime.utcnow() + timedelta(days=37), "Honors College", 40),
    ]
    
    for title, desc, date, location, capacity in events_data:
        event = Event(
            title=title,
            description=desc,
            event_date=date,
            location=location,
            max_attendees=capacity,
            created_at=datetime.utcnow() - timedelta(days=randint(1, 14))
        )
        db.session.add(event)
    
    safe_commit()
    print(f"✅ Created {len(events_data)} events")


def seed_scholarships():
    """Create scholarship opportunities"""
    print("\n🎓 Seeding scholarships...")
    
    scholarships_data = [
        # Academic Excellence (5)
        ("Gorilla Excellence Scholarship", 5000, 
         "Awarded to students with outstanding academic achievement. Minimum 3.8 GPA required. Renewable for up to 4 years with continued academic excellence.",
         "2025-12-31"),
        ("Presidential Scholarship", 8000,
         "Full-tuition scholarship for exceptional students. Must maintain 3.9 GPA. Leadership experience required.",
         "2026-02-15"),
        ("Dean's List Achievement Award", 3000,
         "For students who made Dean's List 3+ consecutive semesters. Minimum 3.5 GPA.",
         "2025-11-30"),
        ("Academic Distinction Grant", 2500,
         "Merit-based award for high-achieving students in all majors. 3.6 GPA minimum.",
         "2026-01-20"),
        ("Honors Program Scholarship", 4000,
         "Exclusively for Honors Program students. Requires 3.7 GPA and research project.",
         "2025-12-15"),
        
        # STEM Fields (6)
        ("STEM Leadership Award", 3000,
         "For students in Science, Technology, Engineering, and Mathematics fields. Must demonstrate leadership in STEM organizations or research.",
         "2025-11-30"),
        ("Computer Science Innovation Grant", 4500,
         "For CS students with exceptional programming projects or hackathon participation. Portfolio required.",
         "2026-01-15"),
        ("Engineering Excellence Award", 5000,
         "For engineering students with strong academic record and hands-on project experience. 3.5 GPA minimum.",
         "2025-12-20"),
        ("Women in Technology Scholarship", 3500,
         "Supporting women pursuing careers in technology. Open to CS, IT, and related majors.",
         "2026-02-01"),
        ("Mathematics Achievement Award", 2500,
         "For mathematics majors with strong analytical skills and research experience.",
         "2026-01-10"),
        ("Biology Research Grant", 3000,
         "For biology students engaged in faculty-led research projects. Lab experience required.",
         "2025-12-31"),
        
        # Business & Social Sciences (4)
        ("Business Leadership Scholarship", 4000,
         "For business students demonstrating leadership potential. Involvement in business clubs encouraged.",
         "2026-01-25"),
        ("Entrepreneurship Award", 3500,
         "For students with startup ideas or small business experience. Business plan required.",
         "2025-12-10"),
        ("Psychology Research Grant", 2500,
         "For psychology majors involved in research projects. Faculty recommendation required.",
         "2026-02-05"),
        ("Communication Excellence Award", 2000,
         "For communication students with strong portfolios. Journalism, PR, or media focus.",
         "2025-12-31"),
        
        # Healthcare & Nursing (3)
        ("Nursing Excellence Scholarship", 4500,
         "For nursing students with clinical experience and strong academic records. 3.5 GPA minimum.",
         "2026-01-15"),
        ("Healthcare Leadership Award", 3500,
         "For students pursuing healthcare careers. Volunteer experience in medical settings required.",
         "2025-12-20"),
        ("Allied Health Professions Grant", 2500,
         "For students in allied health programs (PT, OT, lab tech, etc.). Clinical hours documented.",
         "2026-02-01"),
        
        # Special Populations (6)
        ("First Generation Scholarship", 4000,
         "For first-generation college students. Essay about family's educational journey required.",
         "2025-12-15"),
        ("Non-Traditional Student Award", 3000,
         "For students age 25+ returning to complete their degree. Part-time students eligible.",
         "2026-01-30"),
        ("Transfer Student Success Grant", 2500,
         "For transfer students with strong GPA from previous institution. Minimum 3.3 GPA.",
         "2025-12-31"),
        ("International Student Scholarship", 3500,
         "For international students maintaining F-1 visa status. Cultural involvement encouraged.",
         "2026-01-15"),
        ("Veterans Education Award", 4000,
         "For military veterans and active duty service members. DD-214 or military ID required.",
         "2025-11-30"),
        ("Single Parent Success Grant", 2500,
         "Supporting single parents pursuing higher education. Financial need considered.",
         "2026-02-10"),
        
        # Community & Service (4)
        ("Community Service Grant", 2000,
         "For students with significant volunteer experience. Minimum 100 service hours required.",
         "2026-01-15"),
        ("Campus Involvement Award", 2500,
         "For students active in multiple student organizations. Leadership roles preferred.",
         "2025-12-31"),
        ("Diversity & Inclusion Scholarship", 3000,
         "Supporting diversity initiatives on campus. Essay on inclusion efforts required.",
         "2026-01-20"),
        ("Peer Mentor Excellence Award", 1500,
         "For students serving as peer mentors or tutors. Must complete mentor training.",
         "2026-02-15"),
        
        # Athletics & Arts (3)
        ("Athletics Scholarship", 6000,
         "For student athletes in good academic standing. NCAA eligibility required. Renewable annually.",
         "2026-02-01"),
        ("Performing Arts Excellence Award", 2500,
         "For music, theatre, or dance students. Audition or portfolio required.",
         "2025-12-15"),
        ("Creative Arts Grant", 2000,
         "For visual arts students with strong portfolios. Gallery exhibition encouraged.",
         "2026-01-30"),
    ]
    
    for name, amount, desc, deadline in scholarships_data:
        scholarship = Scholarship(
            name=name,
            amount=amount,
            description=desc,
            deadline=datetime.strptime(deadline, "%Y-%m-%d").date(),
            requirements=desc,  # Using full description as requirements
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
        # Tech/CS Success Stories
        ("From PSU to Silicon Valley", 
         "After graduating with a Computer Science degree from PSU in 2020, I landed my dream job at Google as a Software Engineer. The foundation I received at PSU was incredible - professors who actually cared about my success, hands-on projects that built my portfolio, and career services that helped me prep for technical interviews. I'm now working on machine learning projects that impact millions of users daily. PSU prepared me better than many of my colleagues from 'bigger name' schools. Forever a proud Gorilla!"),
        
        ("Building the Next Big App",
         "As a CS student at PSU, I started coding my first mobile app in my dorm room. Fast forward 3 years - that app now has 2 million downloads and just secured Series A funding! PSU's entrepreneurship program connected me with mentors who guided me through the startup process. The Computer Science curriculum gave me the technical skills, but the supportive PSU community gave me the confidence to take the leap. Now I'm hiring PSU grads for my growing team!"),
        
        ("From Intern to Tech Lead",
         "I graduated PSU in 2019 with a degree in Technology. Started as an intern at a local tech company, and through hard work and the solid foundation PSU gave me, I've risen to Tech Lead managing a team of 8 developers. PSU taught me not just how to code, but how to think critically, solve problems, and communicate effectively. These soft skills have been just as important as technical skills in my career growth. Hiring managers: recruit PSU grads - they're prepared!"),
        
        # Business Success Stories
        ("Starting My Own Business",
         "I used the business skills I learned at PSU to launch my own digital marketing agency right after graduation. The Business Administration program at PSU wasn't just theory - we worked on real client projects, learned actual business software, and networked with local business leaders. Three years later, my agency has 15 employees and serves clients across 3 states. The entrepreneurship courses and faculty mentorship at PSU made this possible. Thank you PSU!"),
        
        ("Corporate Leadership Journey",
         "Graduated PSU with a Business degree in 2018, started in an entry-level analyst role. Today I'm a Regional Manager overseeing 5 locations and 50+ employees. PSU's business program taught me practical skills - financial analysis, team management, strategic planning - that I use every single day. The internship opportunities PSU connected me with gave me real-world experience that set me apart. PSU prepares you for real business challenges, not just exams."),
        
        ("Finance Career Success",
         "From PSU Finance major to Financial Advisor at a major firm managing $50M in assets. PSU gave me the analytical skills and ethical foundation that clients trust. The small class sizes meant professors knew me by name and helped me land my first internship. That internship turned into my career. Now I make it a point to hire PSU interns every summer because I know the quality of education and character they bring."),
        
        # Healthcare Success Stories
        ("Making a Difference in Healthcare",
         "As a PSU Nursing grad (Class of 2021), I'm now working as an RN at one of Kansas City's top hospitals. PSU's nursing program prepared me incredibly well - the clinical rotations gave me confidence, the simulation labs prepared me for real emergencies, and the caring faculty were there every step of the way. I feel like I'm truly making a difference in patients' lives every day. Proud to be a Gorilla Nurse!"),
        
        ("Nurse Practitioner Dream Achieved",
         "Got my BSN from PSU in 2018, worked as an RN for 2 years, then came back for my Master's and NP certification. Now I'm a Family Nurse Practitioner with my own practice! PSU's nursing program gave me the clinical skills and critical thinking I needed. The faculty didn't just teach us nursing - they taught us to be advocates for our patients and ourselves. PSU nurses are known for excellence, and I'm proud to be part of that legacy."),
        
        # Engineering Success Stories
        ("Engineering Innovation",
         "PSU Mechanical Engineering grad here! I'm now a Senior Engineer at a major aerospace company designing components for commercial aircraft. The hands-on labs at PSU, the senior design project, and the internship connections through PSU's career services prepared me perfectly for this role. I've worked with engineers from schools across the country, and I can confidently say PSU engineering grads hold their own anywhere. Go Gorillas!"),
        
        ("From Student to Professional Engineer",
         "Earned my Electrical Engineering degree from PSU and just passed my PE exam! Working for a power utility company as a licensed Professional Engineer. PSU's engineering curriculum was rigorous but practical. Professors had real industry experience and brought that into the classroom. The senior design project I did at PSU is still on my resume 5 years later - it showcases real problem-solving skills that employers love."),
        
        # Career Change Success Stories
        ("Career Change Success",
         "I went back to PSU at age 32 to change careers from retail management to Data Science. Best decision I ever made! PSU welcomed non-traditional students like me. The flexible class schedules, supportive faculty who understood I had a family, and practical curriculum prepared me for my new career. Now I'm a Data Analyst making twice what I made before, and I actually love going to work. It's never too late - PSU proved that to me!"),
        
        ("From Liberal Arts to Tech",
         "Started at PSU as an English major, took one programming class as an elective, and fell in love with coding. PSU's advisors helped me add a CS minor, and I ended up in a software development role after graduation. The combination of communication skills from English and technical skills from CS made me incredibly marketable. I write better documentation than anyone on my team and can explain technical concepts to non-technical stakeholders. PSU's liberal arts foundation + technical skills = career success!"),
        
        # Graduate School Success
        ("PhD Journey",
         "PSU prepared me so well for graduate school! Got my bachelor's in Biology from PSU, then went on to earn my PhD in Molecular Biology from a major research university. The research experience I got at PSU - working one-on-one with professors on real projects - gave me a huge advantage in grad school. Many of my grad school classmates from larger schools had never even met their undergrad professors! PSU's small class sizes and research opportunities are invaluable."),
        
        # Community Impact Success
        ("Giving Back to My Community",
         "PSU taught me the importance of community service and leadership. After graduating with a degree in Social Work, I now direct a nonprofit serving at-risk youth in Southeast Kansas. The skills I learned at PSU - program management, grant writing, community organizing - are what I use every day. More importantly, PSU instilled in me the value of service. I'm making a real impact in my hometown, and that's success to me."),
        
        # Diverse Career Paths
        ("Unexpected Career Path",
         "Graduated with a Psychology degree not sure what I wanted to do. Tried a few different things, and ended up in Human Resources - and I love it! PSU's psychology program taught me about human behavior, motivation, and organizational dynamics. Now I'm an HR Manager helping companies build better workplace cultures. PSU doesn't just prepare you for one job - it teaches you to think, adapt, and succeed in whatever path you choose."),
        
        ("Multi-Industry Success",
         "PSU Business grad working in healthcare administration. PSU taught me that business principles apply everywhere. I've worked in retail, manufacturing, and now healthcare - and the skills PSU gave me have been valuable in every industry. Problem-solving, financial analysis, team leadership - these are universal skills PSU excels at teaching. Don't limit yourself - PSU prepares you for success wherever your career takes you!"),
    ]
    
    for i, (title, content) in enumerate(stories_data):
        if i < len(alumni):
            story = SuccessStory(
                user_id=alumni[i].id,
                title=title,
                content=content,
                created_at=datetime.utcnow() - timedelta(days=randint(30, 365))
            )
            db.session.add(story)
        else:
            # If we run out of alumni users, cycle back to beginning
            story = SuccessStory(
                user_id=alumni[i % len(alumni)].id,
                title=title,
                content=content,
                created_at=datetime.utcnow() - timedelta(days=randint(30, 365))
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
