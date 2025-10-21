# seed_add_missing_models.py
# --------------------------------------------------------------------
# PSU-branded demo seed script for Alumni, Job, Post, and DailyStats
# --------------------------------------------------------------------

from datetime import datetime, timedelta, date
from random import choice, randint
from extensions import db
from models import Alumni, Job, Post, DailyStats, User


def seed_add_missing_models():
    print("🌟 Seeding Alumni, Job, Post, and DailyStats with PSU demo data...")

    # -----------------------------
    # Alumni (PittState graduates)
    # -----------------------------
    alumni_examples = [
        Alumni(
            user_id=None,
            graduation_year="2021",
            employer="Cerner Corporation",
            position="Software Engineer",
            location="Kansas City, MO",
            achievements="Developed patient record integration tools adopted by 20+ hospitals.",
        ),
        Alumni(
            user_id=None,
            graduation_year="2020",
            employer="Koch Industries",
            position="Business Analyst",
            location="Wichita, KS",
            achievements="Led a data optimization project saving $200K annually.",
        ),
        Alumni(
            user_id=None,
            graduation_year="2022",
            employer="Garmin",
            position="UX Designer",
            location="Olathe, KS",
            achievements="Redesigned product UI for aviation line; improved satisfaction by 30%.",
        ),
        Alumni(
            user_id=None,
            graduation_year="2019",
            employer="Pittsburg State University",
            position="Assistant Professor",
            location="Pittsburg, KS",
            achievements="Published 3 research papers on educational technology.",
        ),
        Alumni(
            user_id=None,
            graduation_year="2023",
            employer="Honeywell",
            position="Mechanical Engineer",
            location="Kansas City, MO",
            achievements="Created predictive maintenance models reducing machine downtime by 40%.",
        ),
    ]
    db.session.bulk_save_objects(alumni_examples)

    # -----------------------------
    # Jobs (Career listings)
    # -----------------------------
    jobs = [
        Job(
            title="Marketing Coordinator",
            company="Pittsburg Area Chamber of Commerce",
            description="Coordinate marketing campaigns promoting PSU-community partnerships.",
            location="Pittsburg, KS",
            salary=48000,
            posted_date=datetime.utcnow() - timedelta(days=3),
            deadline=date.today() + timedelta(days=30),
        ),
        Job(
            title="Software Developer Intern",
            company="Cerner Corporation",
            description="Assist with backend Flask APIs for healthcare systems.",
            location="Kansas City, MO",
            salary=22.50,
            posted_date=datetime.utcnow() - timedelta(days=2),
            deadline=date.today() + timedelta(days=15),
        ),
        Job(
            title="Data Analyst",
            company="Kansas City Southern",
            description="Analyze logistics data and present insights to management.",
            location="Kansas City, MO",
            salary=62000,
            posted_date=datetime.utcnow() - timedelta(days=5),
            deadline=date.today() + timedelta(days=25),
        ),
        Job(
            title="Graphic Designer",
            company="Gorilla Creative Studio",
            description="Design promotional materials and PSU student media graphics.",
            location="Pittsburg, KS",
            salary=45000,
            posted_date=datetime.utcnow() - timedelta(days=1),
            deadline=date.today() + timedelta(days=20),
        ),
        Job(
            title="Finance Assistant",
            company="Bicknell Family Center for the Arts",
            description="Support financial planning and event budgeting for campus performances.",
            location="Pittsburg, KS",
            salary=41000,
            posted_date=datetime.utcnow(),
            deadline=date.today() + timedelta(days=28),
        ),
    ]
    db.session.bulk_save_objects(jobs)

    # -----------------------------
    # Posts (Campus feed / insights)
    # -----------------------------
    posts = [
        Post(user_id=None, content="Excited to mentor PSU seniors in software engineering this semester!", category="alumni"),
        Post(user_id=None, content="Join us for the Career Expo next week at the Bicknell Center!", category="event"),
        Post(user_id=None, content="Scholarship deadlines are approaching—check the Scholarship Hub!", category="announcement"),
        Post(user_id=None, content="New Gorilla Scholars leaderboard now live on PittState-Connect!", category="update"),
        Post(user_id=None, content="Congrats to our Tech & Engineering alumni featured in PSU Magazine!", category="news"),
    ]
    db.session.bulk_save_objects(posts)

    # -----------------------------
    # DailyStats (Analytics)
    # -----------------------------
    today = date.today()
    stats = [
        DailyStats(
            date=today - timedelta(days=i),
            active_users=randint(120, 200),
            new_users=randint(5, 20),
            scholarships_applied=randint(2, 15),
            jobs_posted=randint(1, 4),
        )
        for i in range(5)
    ]
    db.session.bulk_save_objects(stats)

    db.session.commit()
    print("✅ Demo data seeded successfully for Alumni, Jobs, Posts, and Analytics!")


if __name__ == "__main__":
    from app_pro import create_app

    app = create_app()
    with app.app_context():
        seed_add_missing_models()
