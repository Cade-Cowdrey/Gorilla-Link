# seed_data.py
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app_pro import create_app, db
from models import (
    User, Profile, Department, Career, Event, AnalyticsRecord
)

app = create_app()

def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Departments
        departments = [
            Department(slug="business", name="Kelce College of Business"),
            Department(slug="nursing", name="School of Nursing"),
            Department(slug="tech", name="Engineering Technology"),
            Department(slug="education", name="College of Education"),
        ]
        db.session.add_all(departments)
        db.session.commit()

        # Careers
        careers = [
            Career(title="Software Engineer", department=departments[2], median_salary=82000, openings=120),
            Career(title="Registered Nurse", department=departments[1], median_salary=68000, openings=200),
            Career(title="Marketing Manager", department=departments[0], median_salary=72000, openings=85),
        ]
        db.session.add_all(careers)
        db.session.commit()

        # Users
        admin = User(email="admin@gorillalink.com", password_hash=generate_password_hash("AdminPass123"), role="admin", is_verified=True)
        student = User(email="student@gorillalink.com", password_hash=generate_password_hash("StudentPass123"), role="student", is_verified=True)
        alumni = User(email="alumni@gorillalink.com", password_hash=generate_password_hash("AlumniPass123"), role="alumni", is_verified=True)
        db.session.add_all([admin, student, alumni])
        db.session.commit()

        # Profiles
        profiles = [
            Profile(user=admin, first_name="Connor", last_name="Vandenberg", department=departments[0], headline="System Admin", major="Business Management", graduation_year=2024, location="Pittsburg, KS"),
            Profile(user=student, first_name="Alex", last_name="Johnson", department=departments[2], headline="Tech Student", major="Engineering Tech", graduation_year=2026, location="Pittsburg, KS"),
            Profile(user=alumni, first_name="Sarah", last_name="Lopez", department=departments[1], headline="Registered Nurse", major="Nursing", graduation_year=2020, location="Kansas City, MO"),
        ]
        db.session.add_all(profiles)
        db.session.commit()

        # Events
        events = [
            Event(slug="career-fair-2025", title="Career Fair 2025", description="Meet employers and network with alumni.", start_time=datetime.utcnow() + timedelta(days=7), end_time=datetime.utcnow() + timedelta(days=7, hours=4), location="Weede Gym", created_by_id=admin.id),
            Event(slug="alumni-weekend", title="Alumni Weekend", description="Reconnect and celebrate with fellow Gorillas!", start_time=datetime.utcnow() + timedelta(days=30), end_time=datetime.utcnow() + timedelta(days=30, hours=5), location="Overman Student Center", created_by_id=admin.id),
        ]
        db.session.add_all(events)
        db.session.commit()

        # Analytics
        analytics = [
            AnalyticsRecord(department_id=departments[0].id, year=2025, placements=80, avg_salary=72000, engagement_rate=78.5),
            AnalyticsRecord(department_id=departments[1].id, year=2025, placements=150, avg_salary=68000, engagement_rate=82.1),
            AnalyticsRecord(department_id=departments[2].id, year=2025, placements=95, avg_salary=81000, engagement_rate=75.0),
        ]
        db.session.add_all(analytics)
        db.session.commit()

        print("✅ Database seeded successfully with demo data.")


if __name__ == "__main__":
    seed()
