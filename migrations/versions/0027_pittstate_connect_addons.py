"""Add PittState-Connect full add-on tables

Revision ID: 0027_pittstate_connect_addons
Revises: 0026_split_user_name_into_first_last
Create Date: 2025-10-21

Note: This migration creates only new tables so it won't affect your existing ones.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0027_pittstate_connect_addons'
down_revision = '0026_split_user_name_into_first_last'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('scholarship',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('amount', sa.Integer()),
        sa.Column('deadline', sa.Date()),
        sa.Column('department', sa.String(length=120)),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'))
    )

    op.create_table('scholarship_application',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), index=True),
        sa.Column('scholarship_id', sa.Integer(), sa.ForeignKey('scholarship.id')),
        sa.Column('status', sa.String(length=32), server_default='draft'),
        sa.Column('progress', sa.Integer(), server_default='0'),
        sa.Column('submitted_at', sa.DateTime())
    )

    op.create_table('essay',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), index=True),
        sa.Column('title', sa.String(length=200)),
        sa.Column('content', sa.Text()),
        sa.Column('last_updated', sa.DateTime())
    )

    op.create_table('reminder',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), index=True),
        sa.Column('scholarship_id', sa.Integer(), nullable=True),
        sa.Column('due_at', sa.DateTime()),
        sa.Column('note', sa.String(length=255))
    )

    op.create_table('financial_literacy_resource',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=200)),
        sa.Column('url', sa.String(length=300)),
        sa.Column('category', sa.String(length=100))
    )

    op.create_table('cost_to_completion',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), index=True),
        sa.Column('estimated_tuition_remaining', sa.Integer(), server_default='0'),
        sa.Column('est_graduation_date', sa.Date())
    )

    op.create_table('funding_journey',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), index=True),
        sa.Column('step', sa.String(length=120)),
        sa.Column('timestamp', sa.DateTime())
    )

    op.create_table('faculty_recommendation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('applicant_user_id', sa.Integer(), index=True),
        sa.Column('faculty_name', sa.String(length=200)),
        sa.Column('file_url', sa.String(length=400))
    )

    op.create_table('leaderboard_entry',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), index=True),
        sa.Column('points', sa.Integer(), server_default='0')
    )

    op.create_table('peer_mentor',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('mentor_user_id', sa.Integer(), index=True),
        sa.Column('mentee_user_id', sa.Integer(), index=True)
    )

    op.create_table('donor',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=200)),
        sa.Column('organization', sa.String(length=200)),
        sa.Column('contact_email', sa.String(length=200))
    )

    op.create_table('donation',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('donor_id', sa.Integer(), sa.ForeignKey('donor.id')),
        sa.Column('amount', sa.Integer()),
        sa.Column('note', sa.String(length=255))
    )

    op.create_table('impact_story',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=200)),
        sa.Column('body', sa.Text()),
        sa.Column('photo_url', sa.String(length=400)),
        sa.Column('published_at', sa.DateTime())
    )

def downgrade():
    op.drop_table('impact_story')
    op.drop_table('donation')
    op.drop_table('donor')
    op.drop_table('peer_mentor')
    op.drop_table('leaderboard_entry')
    op.drop_table('faculty_recommendation')
    op.drop_table('funding_journey')
    op.drop_table('cost_to_completion')
    op.drop_table('financial_literacy_resource')
    op.drop_table('reminder')
    op.drop_table('essay')
    op.drop_table('scholarship_application')
    op.drop_table('scholarship')
