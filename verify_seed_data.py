# verify_seed_data.py
"""
VERIFY SEED DATA for Gorilla-Link / PittState Connect
-----------------------------------------------------
✅ Read-only sanity check — no DB writes or deletions.
✅ Confirms demo records exist for departments, users, profiles, careers,
   events, analytics, and badges.
"""

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


def check_count(model, name: str, min_expected: int = 1):
    count = model.query.count()
    if count >= min_expected:
        print(f"✅ {name}: {count} record(s) found")
    else:
        print(f"⚠️  {name}: only {count} found (expected ≥ {min_expected})")
    return count


def verify():
    with app.app_context():
        print("\n🔍 Verifying Gorilla-Link demo seed data...\n")

        ok = True

        # 1️⃣ Departments
        dept_count = check_count(Department, "Departments", 4)
        if dept_count < 4:
            ok = False

        # 2️⃣ Users
        user_count = check_count(User, "Users", 3)
        for email in ["admin@gorillalink.com", "student@gorillalink.com", "alumni@gorillalink.com"]:
            user = User.query.filter_by(email=email).first()
            if user:
                print(f"   • Found {email} (role={user.role})")
            else:
                print(f"   ⚠️ Missing {email}")
                ok = False

        # 3️⃣ Profiles
        profile_count = check_count(Profile, "Profiles", 3)
        if profile_count < 3:
            ok = False

        # 4️⃣ Careers
        career_count = check_count(Career, "Careers", 3)
        if career_count < 3:
            ok = False

        # 5️⃣ Events
        event_count = check_count(Event, "Events", 2)
        if event_count < 2:
            ok = False

        # 6️⃣ Analytics
        analytics_count = check_count(AnalyticsRecord, "Analytics Records", 4)
        if analytics_count < 4:
            ok = False

        # 7️⃣ Badges
        badge_count = check_count(CareerBadge, "Career Badges", 3)
        if badge_count < 3:
            ok = False

        # 8️⃣ Admin Badge
        admin = User.query.filter_by(email="admin@gorillalink.com").first()
        badge = CareerBadge.query.filter_by(slug="resume-ready").first()
        if admin and badge:
            has_badge = UserBadge.query.filter_by(user_id=admin.id, badge_id=badge.id).first()
            if has_badge:
                print(f"🏅 Admin has Resume Ready badge ✅")
            else:
                print(f"⚠️  Admin missing Resume Ready badge")
                ok = False

        # ✅ Final result
        print("\n-------------------------------------------")
        if ok:
            print("🎉 All demo data verified successfully!")
        else:
            print("⚠️  Some demo data is missing or incomplete. Run seed_addons.py again.")
        print("-------------------------------------------\n")


if __name__ == "__main__":
    verify()
