# seed_addons.py
"""
SAFE IDEMPOTENT SEEDER for Gorilla-Link / PittState Connect
-----------------------------------------------------------
✅ Can run infinite times safely — no duplication, no data loss.
✅ Inserts or updates demo data for Departments, Users, Profiles, Careers, Events, Analytics, and Badges.
"""

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app_pro import create_app, db
from models import (
    User,
    Profile,
    Department,
    Career,
    Event,
    AnalyticsRecord,
    CareerBadge,
    UserBadge,
)

app = create_app()

def get_or_create(model, filters: dict, defaults: dict = None):
    """Fetch object by filters or create it if missing."""
    instance = model.query.filter_by(**filters).first()
    if instance:
        updated = False
        if defaults:
            for key, value in defaults.items():
                if getattr(instance, key, None) != value:
                    setattr(instance, key, value)
                    updated = True
        if updated:
            db.session.commit()
            print(f"🔄 Updated {model.__name__}: {filters}")
        return instance, False
    instance = model(**{**filters, **(defaults or {})})
    db.session.add(instance)
    db.session.commit()
    print(f"✅ Created new {model.__name__}: {filters}")
    return instance, True


def safe_seed():
    with app.app_context():
        print("\n🌱 Starting safe idempotent seed process...\n")

        # -----------------------
        # Departments
        # -----------------------
        departments = [
            {"slug": "business", "name": "Kelce College of Business"},
            {"slug": "nursing", "name": "School of Nursing"},
            {"slug": "tech", "name": "Engineering Technology"},
            {"slug": "education", "name": "College of Education"},
        ]
        for dept_data in departments:
            get_or_create(Department, {"slug": dept_data["slug"]}, {"name": dept_data["name"], "created_at": datetime.utcnow()})

        # -----------------------
        # Users
        # -----------------------
        users = [
            {
                "email": "admin@gorillalink.com",
                "defaults": {
                    "password_hash": generate_password_hash("AdminPass123"),
                    "role": "admin",
                    "is_verified": True,
                },
            },
            {
                "email": "student@gorillalink.com",
                "defaults": {
                    "password_hash": generate_password_hash("StudentPass123"),
                    "role": "student",
                    "is_verified": True,
                },
            },
            {
                "email": "alumni@gorillalink.com",
                "defaults": {
                    "password_hash": generate_password_hash("AlumniPass123"),
                    "role": "alumni",
                    "is_verified": True,
                },
            },
        ]
        for u in users:
            get_or_create(User, {"email": u["email"]}, u["defaults"])

        # -----------------------
        # Profiles
        # -----------------------
        profile_data = [
            {
                "email": "admin@gorillalink.com",
                "first_name": "Connor",
                "last_name": "Vandenberg",
                "headline": "System Admin",
                "major": "Business Management",
                "grad_year": 2024,
                "dept_slug": "business",
            },
            {
                "email": "student@gorillalink.com",
                "first_name": "Alex",
                "last_name": "Johnson",
                "headline": "Tech Student",
                "major": "Engineering Tech",
                "grad_year": 2026,
                "dept_slug": "tech",
            },
            {
                "email": "alumni@gorillalink.com",
                "first_name": "Sarah",
                "last_name": "Lopez",
                "headline": "Registered Nurse",
                "major": "Nursing",
                "grad_year": 2020,
                "dept_slug": "nursing",
            },
        ]

        for p in profile_data:
            user = User.query.filter_by(email=p["email"]).first()
            dept = Department.query.filter_by(slug=p["dept_slug"]).first()
            if not user or not dept:
                continue
            existing = Profile.query.filter_by(user_id=user.id).first()
            if not existing:
                new_profile = Profile(
                    user_id=user.id,
                    first_name=p["first_name"],
                    last_name=p["last_name"],
                    headline=p["headline"],
                    major=p["major"],
                    graduation_year=p["grad_year"],
                    department=dept,
                    created_at=datetime.utcnow(),
                )
                db.session.add(new_profile)
                db.session.commit()
                print(f"✅ Created profile for {p['email']}")
            else:
                # Update department or headline if changed
                changed = False
                if existing.department_id != dept.id:
                    existing.department_id = dept.id
                    changed = True
                if existing.headline != p["headline"]:
                    existing.headline = p["headline"]
                    changed = True
                if changed:
                    db.session.commit()
                    print(f"🔄 Updated profile for {p['email']}")

        # -----------------------
        # Careers
        # -----------------------
        careers = [
            ("Software Engineer", "tech", 82000, 120),
            ("Registered Nurse", "nursing", 68000, 200),
            ("Marketing Manager", "business", 72000, 85),
        ]
        for title, dept_slug, salary, openings in careers:
            dept = Department.query.filter_by(slug=dept_slug).first()
            if not dept:
                continue
            get_or_create(
                Career,
                {"title": title, "dept_id": dept.id},
                {"median_salary": salary, "openings": openings, "updated_at": datetime.utcnow()},
            )

        # -----------------------
        # Events
        # -----------------------
        admin = User.query.filter_by(email="admin@gorillalink.com").first()
        events = [
            {
                "slug": "career-fair-2025",
                "title": "Career Fair 2025",
                "description": "Meet employers and network with alumni.",
                "start_time": datetime.utcnow() + timedelta(days=7),
                "end_time": datetime.utcnow() + timedelta(days=7, hours=4),
                "location": "Weede Gym",
                "created_by_id": admin.id if admin else None,
            },
            {
                "slug": "alumni-weekend",
                "title": "Alumni Weekend",
                "description": "Reconnect and celebrate with fellow Gorillas!",
                "start_time": datetime.utcnow() + timedelta(days=30),
                "end_time": datetime.utcnow() + timedelta(days=30, hours=5),
                "location": "Overman Student Center",
                "created_by_id": admin.id if admin else None,
            },
        ]
        for e in events:
            get_or_create(Event, {"slug": e["slug"]}, e)

        # -----------------------
        # Analytics
        # -----------------------
        for dept in Department.query.all():
            get_or_create(
                AnalyticsRecord,
                {"department_id": dept.id, "year": 2025},
                {
                    "placements": 80 + dept.id * 5,
                    "avg_salary": 70000 + dept.id * 1000,
                    "engagement_rate": 75 + dept.id * 2.5,
                    "updated_at": datetime.utcnow(),
                },
            )

        # -----------------------
        # Badges
        # -----------------------
        badges = [
            ("resume-ready", "Resume Ready", "Uploaded and verified resume."),
            ("mentor-verified", "Mentor Verified", "Approved alumni mentor."),
            ("network-builder", "Network Builder", "Connected with 10+ members."),
        ]
        for slug, label, desc in badges:
            get_or_create(CareerBadge, {"slug": slug}, {"label": label, "description": desc})

        # Give admin a badge (once)
        admin = User.query.filter_by(email="admin@gorillalink.com").first()
        badge = CareerBadge.query.filter_by(slug="resume-ready").first()
        if admin and badge:
            existing = UserBadge.query.filter_by(user_id=admin.id, badge_id=badge.id).first()
            if not existing:
                db.session.add(UserBadge(user_id=admin.id, badge_id=badge.id, granted_at=datetime.utcnow()))
                db.session.commit()
                print("🏅 Admin awarded badge: Resume Ready")

        print("\n🎉 Safe idempotent seed completed successfully.\n")


if __name__ == "__main__":
    safe_seed()
