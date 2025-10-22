# seed_pittstate_connect.py
"""
Seeds PittState-Connect with realistic PSU data.
Creates departments, roles, users, alumni, faculty, students,
companies, jobs, scholarships, donors, and connections.
"""

from datetime import datetime, timedelta, date
from faker import Faker
import random
from models import (
    db, Role, Department, User, Student, Alumni, Faculty,
    Company, AlumniEmployment, Scholarship, ScholarshipApplication,
    Donor, Donation, Job, Event, Group, Connection,
    Mentorship, Badge, Opportunity, Story, UserAnalytics, DailyStats
)
from app_pro import create_app

fake = Faker()
app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    print("🌾 Seeding roles...")
    roles = {
        "student": Role(slug="student", name="Student"),
        "alumni": Role(slug="alumni", name="Alumni"),
        "faculty": Role(slug="faculty", name="Faculty"),
        "admin": Role(slug="admin", name="Administrator")
    }
    db.session.add_all(roles.values())

    print("🏛️ Seeding departments...")
    departments = [
        Department(code="KELCE", name="Kelce College of Business", college="College of Business"),
        Department(code="TECH", name="College of Technology", college="Technology & Workforce Learning"),
        Department(code="EDUC", name="College of Education", college="Education"),
        Department(code="ARTS", name="College of Arts & Sciences", college="Arts & Sciences"),
        Department(code="NURS", name="School of Nursing", college="Health Sciences")
    ]
    db.session.add_all(departments)
    db.session.flush()

    print("👩‍🎓 Seeding users...")
    users = []
    for i in range(10):
        dept = random.choice(departments)
        role = random.choice(list(roles.values()))
        u = User(
            email=f"user{i}@pittstate.edu",
            password_hash=fake.sha256(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            headline=f"Passionate {role.name.lower()} at PSU",
            role=role,
            department=dept,
            bio=fake.paragraph(nb_sentences=3),
            is_verified=True
        )
        users.append(u)
    db.session.add_all(users)
    db.session.flush()

    print("🎓 Students, Alumni, Faculty...")
    for u in users:
        if u.role.slug == "student":
            db.session.add(Student(user=u, grad_year=2026, major="Business Administration", department=u.department))
        elif u.role.slug == "alumni":
            alumni = Alumni(
                user=u, grad_year=2019, degree="B.S. in Marketing", current_title="Account Executive",
                current_company="Watco", department=u.department
            )
            db.session.add(alumni)
            db.session.flush()
            db.session.add(AlumniEmployment(alumni=alumni, company_id=None, title="Sales Associate", is_current=True))
        elif u.role.slug == "faculty":
            db.session.add(Faculty(user=u, title="Assistant Professor", office="Room 214", department=u.department))

    print("🏢 Seeding companies...")
    companies = [
        Company(name="Watco", website="https://www.watco.com", hq_city="Pittsburg", hq_state="KS"),
        Company(name="Garmin", website="https://www.garmin.com", hq_city="Olathe", hq_state="KS"),
        Company(name="Spirit AeroSystems", website="https://www.spiritaero.com", hq_city="Wichita", hq_state="KS"),
        Company(name="H&R Block", website="https://www.hrblock.com", hq_city="Kansas City", hq_state="MO")
    ]
    db.session.add_all(companies)

    print("💼 Seeding jobs...")
    for i in range(5):
        db.session.add(Job(
            title=f"Internship {i + 1}",
            description=fake.paragraph(nb_sentences=5),
            company=random.choice(companies),
            poster=random.choice(users),
            location="Pittsburg, KS",
            is_remote=random.choice([True, False])
        ))

    print("🎓 Seeding scholarships...")
    scholarships = []
    for i in range(5):
        s = Scholarship(
            title=f"PSU Excellence Award {i + 1}",
            description=fake.paragraph(nb_sentences=4),
            amount=random.randint(1000, 5000),
            opens_on=date.today() - timedelta(days=15),
            closes_on=date.today() + timedelta(days=45)
        )
        scholarships.append(s)
    db.session.add_all(scholarships)
    db.session.flush()

    print("📝 Scholarship applications...")
    for s in scholarships:
        db.session.add(ScholarshipApplication(
            scholarship=s,
            applicant=random.choice(users),
            essay_text=fake.paragraph(nb_sentences=6)
        ))

    print("❤️ Seeding donors & donations...")
    donors = [
        Donor(name="Gorilla Alumni Foundation", organization="PSU Alumni", email="donor@psu.edu"),
        Donor(name="Crawford County Bank", organization="Local Partner", email="ccbank@pittsburg.com")
    ]
    db.session.add_all(donors)
    db.session.flush()

    for donor in donors:
        db.session.add(Donation(donor=donor, amount=random.randint(2000, 10000), designated_scholarship=random.choice(scholarships)))

    print("🪙 Badges...")
    badges = [
        Badge(slug="mentor", name="Peer Mentor", description="Helps guide students."),
        Badge(slug="donor", name="Scholarship Donor", description="Contributed to student funding."),
        Badge(slug="leader", name="Campus Leader", description="Active student leader."),
    ]
    db.session.add_all(badges)

    print("📅 Events...")
    for i in range(3):
        db.session.add(Event(
            title=f"Career Fair {2025 + i}",
            description="Connect with employers and PSU alumni.",
            starts_at=datetime.utcnow() + timedelta(days=30 * (i + 1)),
            ends_at=datetime.utcnow() + timedelta(days=30 * (i + 1), hours=2),
            location="Student Center Ballroom",
            organizer=random.choice(users)
        ))

    print("💬 Groups...")
    groups = [
        Group(name="Kelce Business Leaders", description="Network of Kelce business students.", owner=random.choice(users)),
        Group(name="Tech Innovators", description="College of Technology student makerspace.", owner=random.choice(users))
    ]
    db.session.add_all(groups)

    print("🤝 Connections...")
    for _ in range(10):
        requester, addressee = random.sample(users, 2)
        db.session.add(Connection(requester=requester, addressee=addressee, status="accepted"))

    print("🎯 Mentorships...")
    for _ in range(5):
        mentor, mentee = random.sample(users, 2)
        db.session.add(Mentorship(mentor=mentor, mentee=mentee, goals="Career advice and skill development."))

    print("📖 Stories...")
    for _ in range(3):
        db.session.add(Story(
            title=fake.sentence(nb_words=5),
            body=fake.paragraph(nb_sentences=6),
            author=random.choice(users)
        ))

    print("📈 User Analytics & Daily Stats...")
    for u in users:
        db.session.add(UserAnalytics(user=u, connections_count=random.randint(3, 10), posts_count=random.randint(1, 5)))

    db.session.add(DailyStats(
        stats_date=date.today(),
        new_users=len(users),
        new_connections=5,
        new_posts=4,
        new_events=2
    ))

    db.session.commit()
    print("✅ PSU demo data seeded successfully!")
