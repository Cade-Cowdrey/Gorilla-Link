"""Seed demo departments, users, and analytics"""
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app_pro import db
from models import Department, User, UserAnalytics
import random

# revision identifiers
revision = '0004_seed_demo_users'
down_revision = '0003_seed_departments'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    departments = [
        Department(name="Computer Science & Technology", description="Tech-driven innovation."),
        Department(name="Education", description="Preparing future teachers."),
        Department(name="Business & Entrepreneurship", description="Leaders in business."),
        Department(name="Nursing", description="Healthcare professionals."),
    ]
    session.add_all(departments)
    session.commit()

    users = [
        User(name="Cade Cowdrey", email="ccowdrey@pittstate.edu", role="Admin", department=departments[0]),
        User(name="Emily Johnson", email="ejohnson@pittstate.edu", role="Student", department=departments[0]),
        User(name="Jacob Miller", email="jmiller@pittstate.edu", role="Student", department=departments[2]),
        User(name="Sarah Brown", email="sbrown@pittstate.edu", role="Alumni", department=departments[1]),
        User(name="Dr. Alan White", email="awhite@pittstate.edu", role="Faculty", department=departments[3]),
    ]

    for user in users:
        analytics = UserAnalytics(
            user=user,
            profile_views=random.randint(20, 150),
            connections_count=random.randint(1, 15),
            engagement_score=round(random.uniform(1.0, 5.0), 2),
            last_active=datetime.utcnow()
        )
        session.add(user)
        session.add(analytics)

    session.commit()
    print("✅ Seeded demo departments, users, and analytics successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.query(UserAnalytics).delete()
    session.query(User).delete()
    session.query(Department).delete()
    session.commit()
