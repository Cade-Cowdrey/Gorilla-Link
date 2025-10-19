"""Add missing auxiliary models: badges, digests, audit logs, and meta info."""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers
revision = "0014_add_missing_models"
down_revision = "0013_init_core_models"
branch_labels = None
depends_on = None


def upgrade():
    # --- BADGES TABLE ---
    op.create_table(
        "badges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("icon", sa.String(255)),
        sa.Column("category", sa.String(100), default="achievement"),
        sa.Column("created_at", sa.DateTime, default=datetime.utcnow),
    )

    # --- USER BADGES TABLE ---
    op.create_table(
        "user_badges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("badge_id", sa.Integer, sa.ForeignKey("badges.id", ondelete="CASCADE")),
        sa.Column("awarded_at", sa.DateTime, default=datetime.utcnow),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    # --- DIGESTS TABLE ---
    op.create_table(
        "digests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), default="general"),
        sa.Column("published_at", sa.DateTime, default=datetime.utcnow),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
    )

    # --- DIGEST LOGS (email sending logs) ---
    op.create_table(
        "digest_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("digest_id", sa.Integer, sa.ForeignKey("digests.id", ondelete="CASCADE")),
        sa.Column("recipient_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("status", sa.String(50), default="sent"),
        sa.Column("sent_at", sa.DateTime, default=datetime.utcnow),
    )

    # --- AUDIT LOGS TABLE ---
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("target_table", sa.String(100)),
        sa.Column("target_id", sa.Integer),
        sa.Column("timestamp", sa.DateTime, default=datetime.utcnow),
        sa.Column("details", sa.Text),
    )

    # --- META INFO (branding/system constants) ---
    op.create_table(
        "meta_info",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.String(500)),
        sa.Column("last_updated", sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # --- Seed Default PSU Badges ---
    bind = op.get_bind()
    existing_badges = bind.execute(sa.text("SELECT COUNT(*) FROM badges")).scalar() if bind else 0
    if existing_badges == 0:
        badges = [
            ("Founder", "Original Gorilla-Link creator", "fa-crown"),
            ("Mentor", "Guided another student", "fa-handshake"),
            ("Leader", "Hosted a PSU campus event", "fa-users"),
            ("Career Climber", "Applied for 3+ internships", "fa-briefcase"),
            ("Connector", "Formed 5+ new PSU connections", "fa-network-wired"),
        ]
        for name, desc, icon in badges:
            bind.execute(sa.text("""
                INSERT INTO badges (name, description, icon, category, created_at)
                VALUES (:name, :desc, :icon, 'achievement', :created)
            """), {"name": name, "desc": desc, "icon": icon, "created": datetime.utcnow()})
        print("🏅 Seeded default PSU badge set.")

    # --- Seed PSU Meta Info ---
    existing_meta = bind.execute(sa.text("SELECT COUNT(*) FROM meta_info")).scalar() if bind else 0
    if existing_meta == 0:
        meta_defaults = {
            "platform_name": "PittState-Connect",
            "theme_color": "#DAA520",
            "institution": "Pittsburg State University",
            "tagline": "Connecting Gorillas for Life",
            "email_support": "support@pittstate-connect.edu",
        }
        for k, v in meta_defaults.items():
            bind.execute(sa.text("""
                INSERT INTO meta_info (key, value, last_updated)
                VALUES (:k, :v, :now)
            """), {"k": k, "v": v, "now": datetime.utcnow()})
        print("🎓 Seeded PSU meta branding defaults.")

    print("✅ Added all auxiliary PSU models (badges, digests, logs, meta info).")


def downgrade():
    op.drop_table("meta_info")
    op.drop_table("audit_logs")
    op.drop_table("digest_logs")
    op.drop_table("digests")
    op.drop_table("user_badges")
    op.drop_table("badges")
    print("🧹 Removed auxiliary PSU models.")
