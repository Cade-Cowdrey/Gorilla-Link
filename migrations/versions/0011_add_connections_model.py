"""Add Connection model to support user networking"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "0011_add_connection_model"
down_revision = "0010_seed_stats"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("connected_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
    )


def downgrade():
    op.drop_table("connections")
