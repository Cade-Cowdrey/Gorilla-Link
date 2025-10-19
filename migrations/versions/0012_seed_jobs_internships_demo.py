"""Seed demo internship applications and hiring outcomes for PittState-Connect"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

# Revision identifiers
revision = "0012_seed_jobs_internships_demo"
down_revision = "0011_add_connections_model"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # --- Tables ---
    jobs_table = sa.table(
        "jobs",
        sa.column("id", sa.Integer),
        sa.column("title", sa.String),
        sa.column("company", sa.String),
        sa.column("location", sa.String),
        sa.column("job_type", sa.String),
    )

    applications_table = sa.table(
        "applications",
        sa.column("id", sa.Integer),
        sa.column("user_id", sa.Integer),
        sa.column("job_id", sa.Integer),
        sa.column("status", sa.String),
        sa.column("applied_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    # --- Existing data ---
    existing_apps = [
        (r[0], r[1])
        for r in session.execute(sa.text("SELECT user_id, job_id FROM applications")).all()
    ]

    jobs = session.execute(sa.text("SELECT id, title, company FROM jobs")).fetchall()
    job_ids = [j[0] for j in jobs]

    if not job_ids:
        print("⚠️ No jobs found — skipping demo application seeding.")
        return

    # --- Demo data generation ---
    now = datetime.utcnow()
    demo_user_ids = [2, 3, 4, 5, 6, 7, 8]  # demo students & alumni from previous seeds
    statuses = ["applied", "interview", "offer", "hired"]

    demo_applications = []
    for i, user_id in enumerate(demo_user_ids):
        job_id = random.choice(job_ids)
        status = random.choice(statuses)
        applied_at = now - timedelta(days=random.randint(5, 30))
        updated_at = applied_at + timedelta(days=random.randint(1, 10))

        if (user_id, job_id) not in existing_apps:
            demo_applications.append(
                {
                    "user_id": user_id,
                    "job_id": job_id,
                    "status": status,
                    "applied_at": applied_at,
                    "updated_at": updated_at,
                }
            )

    if demo_applications:
        session.execute(applications_table.insert(), demo_applications)
        session.commit()
        print(f"✅ Seeded {len(demo_applications)} PSU demo job applications successfully.")
    else:
        print("ℹ️ No new demo applications inserted (data already present).")

    # --- Optional: Insert analytics trend data ---
    stats_table = sa.table(
        "stats",
        sa.column("category", sa.String),
        sa.column("label", sa.String),
        sa.column("value", sa.Float),
        sa.column("last_updated", sa.DateTime),
        sa.column("description", sa.Text),
    )

    metrics = {
        "New Applications This Month": 24,
        "Students Hired": 9,
        "Interview Success Rate": 68.2,
        "Top Employer Partners": 5,
    }

    existing_labels = [
        r[0] for r in session.execute(sa.text("SELECT label FROM stats")).all()
    ]

    for label, value in metrics.items():
        if label not in existing_labels:
            session.execute(
                stats_table.insert().values(
                    category="career_trends",
                    label=label,
                    value=value,
                    last_updated=now,
                    description=f"Auto-generated metric: {label} ({value}).",
                )
            )

    session.commit()
    print("📊 Added PSU career trend analytics to stats table.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(sa.text("""
        DELETE FROM applications WHERE user_id IN (2,3,4,5,6,7,8);
        DELETE FROM stats WHERE category = 'career_trends';
    """))
    session.commit()
    print("🧹 Removed PSU demo job applications and career trend stats.")
