# seed_pittstate_connect_full.py
# ---------------------------------------------------------------
# Full PSU-branded seeding script for PittState-Connect
# Populates Users, Roles, Departments, Alumni, Jobs, Posts,
# Scholarships, Analytics, and Gorilla Scholars mock data.
# ---------------------------------------------------------------

from datetime import datetime, timedelta, date
from random import choice, randint
from extensions import db
from models import (
    User, Role, Department, Alumni, Job, Post, DailyStats, Scholarship
)


# ---------------------------------------------------------------
# Helper: Safe commit wrapper
# ---------------------------------------------------------------
def safe_commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Commit failed: {e}")


# ---------------------------------------------------------------
# 1️⃣ Seed Roles
# ---------------------------------------------------------------
def seed_roles():
    print("➡️ Seeding roles...")
    roles = [
        Role(name="Admin"),
        Role(name="Student"),
        Role(name="Faculty"),
        Role(name="Alumni"),
        Role(name="Employer"),
    ]
    db.session.bulk_save_objects(roles)
    safe_commit()
    print("✅ Roles seeded.")


# ---------------------------------------------------------------
# 2️⃣ Seed Departments
# ---------------------------------------------------------------
def seed_departments():
    print("➡️ Seeding departments...")
    psu_departments = [
        "Kelce College of Business",
        "College of Technology",
        "College of Education",
        "College of Arts and Sciences",
        "School of Nursing",
        "Honors College",
        "Graduate and Continuing Studies",
    ]
    for dept in psu_departments:
        db.session.add(Department(name=dept))
    safe_commit()
    print("✅ Departments seeded.")


# ---------------------------------------------------------------
# 3️⃣ Seed Users (sample faculty, students, alumni)
# ---------------------------------------------------------------
def seed_users():
    print("➡️ Seeding users...")
    users = [
        User(first_name="Avery", last_name="Johnson", email="avery.johnson@pittstate.edu", role_id=2),
        User(first_name="Michael", last_name="Smith", email="michael.smith@pittstate.edu", role_id=2),
        User(first_name="Rachel", last_name="Garcia", email="rachel.garcia@pittstate.edu", role_id=3),
        User(first_name="Ethan", last_name="Miller", email="ethan.miller@pittstate.edu", role_id=4),
        User(first_name="Sophia", last_name="Taylor", email="sophia.taylor@pittstate.edu", role_id=5),
    ]
    db.session.bulk_save_objects(users)
    safe_commit()
    print("✅ Users seeded.")


# ---------------------------------------------------------------
# 4️⃣ Seed Alumni, Jobs, Posts, and DailyStats
# ---------------------------------------------------------------
def seed_alumni_jobs_posts_analytics():
    print("➡️ Seeding Alumni, Jobs, Posts, and Analytics...")

    users = User.query.all()
    if not users:
        print("⚠️ No users found — please seed users first.")
        return

    alumni_list = [
        Alumni(
            user_id=choice(users).id,
            graduation_year="2022",
            employer="Garmin",
            position="UX Designer",
            location="Olathe, KS",
            achievements="Improved navigation systems for aviation interfaces.",
        ),
        Alumni(
            user_id=choice(users).id,
            graduation_year="2021",
            employer="Koch Industries",
            position="Data Engineer",
            location="Wichita, KS",
            achievements="Built analytics pipeline for real-time business insights.",
        ),
        Alumni(
            user_id=choice(users).id,
            graduation_year="2023",
            employer="Honeywell",
            position="Mechanical Engineer",
            location="Kansas City, MO",
            achievements="Reduced production cost by 12% with automated systems.",
        ),
    ]
    db.session.bulk_save_objects(alumni_list)

    jobs = [
        Job(
            title="Software Developer Intern",
            company="Cerner Corporation",
            description="Assist in developing Python APIs for healthcare data.",
            location="Kansas City, MO",
            salary=22.50,
            posted_date=datetime.utcnow() - timedelta(days=3),
            deadline=date.today() + timedelta(days=30),
        ),
        Job(
            title="Marketing Coordinator",
            company="Pittsburg Area Chamber of Commerce",
            description="Promote Pitt State partnerships through media campaigns.",
            location="Pittsburg, KS",
            salary=47000,
            posted_date=datetime.utcnow() - timedelta(days=5),
            deadline=date.today() + timedelta(days=25),
        ),
    ]
    db.session.bulk_save_objects(jobs)

    posts = [
        Post(user_id=choice(users).id, content="PSU Career Fair starts Monday! 🦍", category="event"),
        Post(user_id=choice(users).id, content="Congrats to our new Gorilla Scholars!", category="news"),
        Post(user_id=choice(users).id, content="New alumni mentorships available in Tech & Business.", category="update"),
    ]
    db.session.bulk_save_objects(posts)

    today = date.today()
    analytics = [
        DailyStats(
            date=today - timedelta(days=i),
            active_users=randint(100, 180),
            new_users=randint(5, 15),
            scholarships_applied=randint(1, 10),
            jobs_posted=randint(0, 3),
        )
        for i in range(7)
    ]
    db.session.bulk_save_objects(analytics)

    safe_commit()
    print("✅ Alumni, Jobs, Posts, and Analytics seeded.")


# ---------------------------------------------------------------
# 5️⃣ Seed Scholarships (Phase 2 Smart Match-ready)
# ---------------------------------------------------------------
def seed_scholarships():
    print("➡️ Seeding scholarships...")
    scholarships = [
        Scholarship(
            name="Gorilla Pride Scholarship",
            description="Awarded to students demonstrating leadership and academic excellence.",
            amount=2000,
            deadline=date.today() + timedelta(days=45),
        ),
        Scholarship(
            name="Kelce Business Innovation Grant",
            description="For business students developing entrepreneurial projects.",
            amount=3000,
            deadline=date.today() + timedelta(days=30),
        ),
        Scholarship(
            name="STEM Excellence Award",
            description="Recognizing outstanding achievement in science and technology fields.",
            amount=3500,
            deadline=date.today() + timedelta(days=60),
        ),
    ]
    db.session.bulk_save_objects(scholarships)
    safe_commit()
    print("✅ Scholarships seeded.")


# ---------------------------------------------------------------
# 6️⃣ Run all in order
# ---------------------------------------------------------------
def run_full_seed():
    print("🚀 Running full PittState-Connect seed process...")
    seed_roles()
    seed_departments()
    seed_users()
    seed_alumni_jobs_posts_analytics()
    seed_scholarships()
    print("🎉 Full PSU database seeded successfully!")


# ---------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------
if __name__ == "__main__":
    from app_pro import create_app

    app = create_app()
    with app.app_context():
        run_full_seed()
