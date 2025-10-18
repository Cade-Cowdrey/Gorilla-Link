# seed_check.py
"""
AUTO-SEED-AND-VERIFY for Gorilla-Link / PittState Connect
---------------------------------------------------------
✅ Safely seeds missing demo data (departments, users, profiles, events, analytics, badges)
✅ Immediately verifies all required demo data exists
✅ Fully idempotent — can run infinite times without duplicates or data loss
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


# --------------------------
# Utilities
# --------------------------
def get_or_create(model, filters: dict, defaults: dict = None):
    """Fetch object by filters or create it if missing."""
    instance = model.query.filter_by(**filters).first()
    if instance:
        # optional updates
        if defaults:
            for key, value in defaults.items():
                if getattr(instance, key, None) != value:
                    setattr(instance, key, value)
        return instance, False
    instance = model(**{**filters, **(defaults or {})})
    db.session.add(instance)
    db.session.commit()
    print(f"✅ Created {model.__name__}: {filters}")
    return instance, True


def check_count(model, name: str, min_expected: int = 1):
    """Verify record counts."""
    count = model.query.count()
    status = "✅" if count >= min_expected else "⚠️"
    print(f"{status} {name}: {count} record(s)")
    return count >= min_expected


# --------------------------
# Seeder
# --------------------------
def safe_seed():
    print("\n🌱 Seeding missing demo data (idempotent)...\n")

    # Departments
    departments = [
        {"slug": "business", "name": "Kelce College of Business"},
        {"slug": "nursing", "name": "School of Nursing"},
        {"slug": "tech", "name": "Engineering Technology"},
        {"slug": "education", "name": "College of Education"},
    ]
    for d in departments:
        get_or_create(Department, {"slug": d["slug"]}, {"name": d["name"], "created_at": datetime.utcnow()})

    # Users
    users = [
        ("admin@gorillalink.com", "AdminPass123", "admin"),
        ("student@gorillalink.com", "StudentPass123", "student"),
        ("alumni@gorillalink.com", "AlumniPass123", "alumni"),
    ]
    for email, pw, role in users:
        get_or_create(
            User,
            {"email": email},
            {"password_hash": generate_password_hash(pw), "role": role, "is_verified": True},
        )

    # Profiles
    profiles = [
        ("admin@gorillalink.com", "Connor", "Vandenberg", "System Admin", "Business Management", 2024, "business"),
        ("student@gorillalink.com", "Alex", "Johnson", "Tech Student", "Engineering Tech", 2026, "tech"),
        ("alumni@gorillalink.com", "Sarah", "Lopez", "Registered Nurse", "Nursing", 2020, "nursing"),
    ]
    for email, fn, ln, headline, major, grad, slug in profiles:
        user = User.query.filter_by(email=email).first()
        dept = Department.query.filter_by(slug=slug).first()
        if user and dept:
            existing = Profile.query.filter_by(user_id=user.id).first()
            if not existing:
                db.session.add(
                    Profile(
                        user_id=user.id,
                        first_name=fn,
                        last_name=ln,
                        headline=headline,
                        major=major,
                        graduation_year=grad,
                        department=dept,
                        created_at=datetime.utcnow(),
                    )
                )
                db.session.commit()
                print(f"✅ Created profile for {email}")

    # Careers
    careers = [
        ("Software Engineer", "tech", 82000, 120),
        ("Registered Nurse", "nursing", 68000, 200),
        ("Marketing Manager", "business", 72000, 85),
    ]
    for title, slug, salary, openings in careers:
        dept = Department.query.filter_by(slug=slug).first()
        if dept:
            get_or_create(
                Career,
                {"title": title, "dept_id": dept.id},
                {"median_salary": salary, "openings": openings, "updated_at": datetime.utcnow()},
            )

    # Events
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

    # Analytics
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

    # Badges
    badges = [
        ("resume-ready", "Resume Ready", "Uploaded and verified resume."),
        ("mentor-verified", "Mentor Verified", "Approved alumni mentor."),
        ("network-builder", "Network Builder", "Connected with 10+ members."),
    ]
    for slug, label, desc in badges:
        get_or_create(CareerBadge, {"slug": slug}, {"label": label, "description": desc})

    # Admin badge
    admin = User.query.filter_by(email="admin@gorillalink.com").first()
    badge = CareerBadge.query.filter_by(slug="resume-ready").first()
    if admin and badge:
        existing = UserBadge.query.filter_by(user_id=admin.id, badge_id=badge.id).first()
        if not existing:
            db.session.add(UserBadge(user_id=admin.id, badge_id=badge.id, granted_at=datetime.utcnow()))
            db.session.commit()
            print("🏅 Admin awarded Resume Ready badge")

    print("\n🌿 Seeding complete. Proceeding to verification...\n")


# --------------------------
# Verifier
# --------------------------
def verify():
    ok = True
    print("🔍 Verifying seeded data...\n")

    if not check_count(Department, "Departments", 4):
        ok = False
    if not check_count(User, "Users", 3):
        ok = False
    if not check_count(Profile, "Profiles", 3):
        ok = False
    if not check_count(Career, "Careers", 3):
        ok = False
    if not check_count(Event, "Events", 2):
        ok = False
    if not check_count(AnalyticsRecord, "Analytics Records", 4):
        ok = False
    if not check_count(CareerBadge, "Career Badges", 3):
        ok = False

    admin = User.query.filter_by(email="admin@gorillalink.com").first()
    badge = CareerBadge.query.filter_by(slug="resume-ready").first()
    if admin and badge:
        has_badge = UserBadge.query.filter_by(user_id=admin.id, badge_id=badge.id).first()
        if has_badge:
            print("🏅 Admin has Resume Ready badge ✅")
        else:
            print("⚠️ Admin missing Resume Ready badge")
            ok = False

    print("\n-------------------------------------------")
    if ok:
        print("🎉 All demo data verified successfully!")
    else:
        print("⚠️ Some demo data missing. Re-run seed_check.py to fix.")
    print("-------------------------------------------\n")


# --------------------------
# Main Runner
# --------------------------
if __name__ == "__main__":
    with app.app_context():
        safe_seed()
        verify()
