"""Seed a sensible default set of badges (skips if any already exist)."""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = "0017_seed_default_badges"
down_revision = "0016_add_badge_models"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "badges" not in insp.get_table_names():
        return

    count = bind.execute(sa.text("SELECT COUNT(*) FROM badges")).scalar() or 0
    if count > 0:
        return

    rows = [
        ("Founder", "founder", "Original Gorilla-Link creator", "fa-crown"),
        ("Mentor", "mentor", "Guided another student", "fa-handshake"),
        ("Leader", "leader", "Hosted a PSU campus event", "fa-users"),
        ("Career Climber", "career-climber", "Applied for 3+ internships", "fa-briefcase"),
        ("Connector", "connector", "Formed 5+ new PSU connections", "fa-network-wired"),
    ]
    for name, slug, desc, icon in rows:
        bind.execute(
            sa.text(
                """
                INSERT INTO badges (name, slug, description, icon, category, is_active, created_at)
                VALUES (:n, :s, :d, :i, 'achievement', true, :ts)
                """
            ),
            {"n": name, "s": slug, "d": desc, "i": icon, "ts": datetime.utcnow()},
        )


def downgrade():
    # Non-destructive: keep seeded rows.
    pass
