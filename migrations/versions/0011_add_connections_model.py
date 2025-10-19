"""Add and seed PSU-branded connections model for Gorilla-Link / PittState-Connect"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Revision identifiers
revision = "0011_add_connections_model"
down_revision = "0010_seed_stats"
branch_labels = None
depends_on = None


def upgrade():
    # --- 1️⃣ Create table if not exists ---
    op.create_table(
        "connections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("connection_id", sa.Integer, nullable=False),
        sa.Column("status", sa.String(length=20), default="connected"),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "connection_id", name="uq_user_connection")
    )

    # --- 2️⃣ Seed demo PSU-style relationships ---
    bind = op.get_bind()
    session = Session(bind=bind)

    connections_table = sa.table(
        "connections",
        sa.column("user_id", sa.Integer),
        sa.column("connection_id", sa.Integer),
        sa.column("status", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    # Check for duplicates before seeding
    existing = [
        (r[0], r[1])
        for r in session.execute(sa.text("SELECT user_id, connection_id FROM connections")).all()
    ]

    now = datetime.utcnow()

    demo_connections = [
        # Faculty-student mentorship links
        {"user_id": 1, "connection_id": 2, "status": "connected"},
        {"user_id": 2, "connection_id": 1, "status": "connected"},

        # Alumni-student mentoring
        {"user_id": 3, "connection_id": 4, "status": "connected"},
        {"user_id": 4, "connection_id": 3, "status": "connected"},

        # Cross-department collaboration
        {"user_id": 5, "connection_id": 2, "status": "connected"},
        {"user_id": 2, "connection_id": 5, "status": "connected"},

        # Student-to-student networking
        {"user_id": 6, "connection_id": 7, "status": "pending"},
        {"user_id": 7, "connection_id": 6, "status": "requested"},

        # Alumni to faculty connections
        {"user_id": 8, "connection_id": 2, "status": "connected"},
        {"user_id": 2, "connection_id": 8, "status": "connected"},

        # Department head to student group
        {"user_id": 9, "connection_id": 1, "status": "connected"},
        {"user_id": 1, "connection_id": 9, "status": "connected"},

        # Local business mentor (PSU partner)
        {"user_id": 10, "connection_id": 3, "status": "connected"},
        {"user_id": 3, "connection_id": 10, "status": "connected"},
    ]

    # Insert only new connections
    for c in demo_connections:
        pair = (c["user_id"], c["connection_id"])
        if pair not in existing:
            session.execute(connections_table.insert().values(
                **c,
                created_at=now - timedelta(days=3),
                updated_at=now - timedelta(days=1)
            ))

    session.commit()
    print("✅ Created and seeded PSU-branded demo connections successfully.")


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # Safely drop table on downgrade
    op.drop_table("connections")

    session.commit()
    print("🧹 Dropped connections table and demo data.")
