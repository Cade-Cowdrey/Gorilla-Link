# ============================================================
# 🌱 PittState-Connect Database Seeder (Safe & Idempotent)
# ============================================================
from datetime import datetime, timedelta
from extensions import db
from app_pro import app
from models import (
    User, Department, Post, Event, Notification,
    Badge, UserBadge, DigestArchive
)

# ------------------------------------------------------------
# 🛡️ Helper functions
# ------------------------------------------------------------
def safe_commit():
    """Commit with rollback safety."""
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Commit failed: {e}")

def get_or_create(model, defaults=None, **kwargs):
    """Return existing row or create a new one."""
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = dict((k, v) for k, v in kwargs.items())
    if defaults:
        params.update(defaults)
    instance = model(**params)
    db.session.add(instance)
    safe_commit()
    return instance, True


# ------------------------------------------------------------
# 👑 1. Admin User
# ------------------------------------------------------------
def seed_admin():
    admin, created = get_or_create(
        User,
        name="Admin User",
        email="admin@pittstate.edu",
        role="admin"
    )
    if created:
        admin.set_password("gorillalink2025")
        db.session.add(admin)
        safe_commit()
        print("✅ Admin account created.")
    else:
        print("ℹ️ Admin account already exists.")


# ------------------------------------------------------------
# 🏫 2. Departments
# ------------------------------------------------------------
def seed_departments():
    dept_names = [
        "Computer Science", "Engineering Technology", "Business Administration",
        "Education", "Psychology & Counseling", "Nursing",
        "Marketing & Management", "Communication", "Art & Design"
    ]
    for name in dept_names:
        get_or_create(Department, name=name)
    print(f"✅ Seeded {len(dept_names)} departments.")


# ------------------------------------------------------------
# 👥 3. Demo Users
# ------------------------------------------------------------
def seed_demo_users():
    sample_users = [
        ("Alex Johnson", "alex@pittstate.edu", "student"),
        ("Emily Smith", "emily@alumni.pittstate.edu", "alumni"),
        ("Jordan Lee", "jordan@pittstate.edu", "student")
    ]
    for name, email, role in sample_users:
        user, created = get_or_create(User, name=name, email=email, role=role)
        if created:
            user.set_password("demo123")
            db.session.add(user)
    safe_commit()
    print(f"✅ Seeded {len(sample_users)} demo users.")


# ------------------------------------------------------------
# 💬 4. Posts
# ------------------------------------------------------------
def seed_demo_posts():
    author = User.query.filter_by(email="alex@pittstate.edu").first()
    if not author:
        print("⚠️ Skipped posts — no author found.")
        return
    posts = [
        Post(content="Excited to connect with PSU alumni!", author=author),
        Post(content="Does anyone know internship openings for CS majors?", author=author)
    ]
    db.session.add_all(posts)
    safe_commit()
    print("✅ Seeded demo posts.")


# ------------------------------------------------------------
# 📅 5. Events
# ------------------------------------------------------------
def seed_events():
    events = [
        Event(
            title="Career Fair 2025",
            description="Meet recruiters and network with PSU alumni.",
            location="PSU Student Center",
            start_time=datetime.utcnow() + timedelta(days=5),
            end_time=datetime.utcnow() + timedelta(days=5, hours=3)
        ),
        Event(
            title="Alumni Networking Mixer",
            description="An evening to reconnect and share success stories.",
            location="Overman Ballroom",
            start_time=datetime.utcnow() + timedelta(days=10),
            end_time=datetime.utcnow() + timedelta(days=10, hours=2)
        )
    ]
    db.session.add_all(events)
    safe_commit()
    print("✅ Seeded demo events.")


# ------------------------------------------------------------
# 🏅 6. Badges
# ------------------------------------------------------------
def seed_badges():
    badges = [
        ("Gorilla Pioneer", "First to join PittState-Connect", "pioneer.png"),
        ("Career Climber", "Posted your first internship", "career.png"),
        ("Community Builder", "Connected with 5 Gorillas", "network.png")
    ]
    for name, desc, icon in badges:
        get_or_create(Badge, name=name, description=desc, icon=icon)
    print("✅ Seeded default badges.")


# ------------------------------------------------------------
# 📰 7. Digest Archives
# ------------------------------------------------------------
def seed_digests():
    digest, created = get_or_create(
        DigestArchive,
        subject="Welcome to PittState-Connect!",
        defaults={
            "content_html": "<h1>Welcome to the PSU Gorilla Network!</h1><p>Stay tuned for weekly updates.</p>",
            "audience": "all"
        }
    )
    if created:
        print("✅ Added initial digest archive.")
    else:
        print("ℹ️ Digest archive already exists.")


# ------------------------------------------------------------
# 🚀 Main runner
# ------------------------------------------------------------
def run_seed():
    with app.app_context():
        print("🌱 Starting PittState-Connect seeding process...")
        seed_admin()
        seed_departments()
        seed_demo_users()
        seed_demo_posts()
        seed_events()
        seed_badges()
        seed_digests()
        print("✅ All seed data inserted successfully.")


if __name__ == "__main__":
    run_seed()
