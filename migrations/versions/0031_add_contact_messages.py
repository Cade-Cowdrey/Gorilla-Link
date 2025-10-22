"""Add ContactMessage model"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = "0031_add_contact_messages"
down_revision = "0030_future_template"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "contact_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table("contact_messages")
