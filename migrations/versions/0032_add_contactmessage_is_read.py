"""Add is_read column to ContactMessage"""
from alembic import op
import sqlalchemy as sa

revision = "0032_add_contactmessage_is_read"
down_revision = "0031_add_contact_messages"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("contact_messages", sa.Column("is_read", sa.Boolean(), nullable=True, server_default="false"))

def downgrade():
    op.drop_column("contact_messages", "is_read")
