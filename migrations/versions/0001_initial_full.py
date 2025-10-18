"""Initial full schema for PittState Connect"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_full'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(150), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256)),
        sa.Column('role', sa.String(50), default='student'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('student_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Create opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(150), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('department_id', sa.Integer, sa.ForeignKey('departments.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Create alumni table
    op.create_table(
        'alumni',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('company', sa.String(150)),
        sa.Column('position', sa.String(150)),
        sa.Column('grad_year', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Create activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now())
    )


def downgrade():
    op.drop_table('activity_logs')
    op.drop_table('alumni')
    op.drop_table('opportunities')
    op.drop_table('departments')
    op.drop_table('users')
