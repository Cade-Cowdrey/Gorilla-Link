"""Add resume and career development models

Revision ID: add_career_features
Revises: 
Create Date: 2025-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_career_features'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create resume_templates table
    op.create_table('resume_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preview_image', sa.String(length=512), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('color_scheme', sa.String(length=50), nullable=True),
        sa.Column('font_family', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('share_token', sa.String(length=64), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=True),
        sa.Column('downloads_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['resume_templates.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_share_token'), 'resumes', ['share_token'], unique=True)
    
    # Create resume_sections table
    op.create_table('resume_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('section_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create mock_interviews table
    op.create_table('mock_interviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('interview_type', sa.String(length=50), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_responses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_feedback', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create career_assessments table
    op.create_table('career_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assessment_type', sa.String(length=50), nullable=True),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create skill_endorsements table
    op.create_table('skill_endorsements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(length=100), nullable=False),
        sa.Column('endorser_id', sa.Integer(), nullable=False),
        sa.Column('proficiency_level', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['endorser_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create learning_resources table
    op.create_table('learning_resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('url', sa.String(length=512), nullable=True),
        sa.Column('provider', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('duration_hours', sa.Float(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_courses table
    op.create_table('user_courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('progress_percent', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('certificate_url', sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(['resource_id'], ['learning_resources.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create industry_insights table
    op.create_table('industry_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('insight_type', sa.String(length=50), nullable=True),
        sa.Column('data_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('views_count', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create company_reviews table
    op.create_table('company_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.String(length=200), nullable=True),
        sa.Column('rating_overall', sa.Float(), nullable=True),
        sa.Column('rating_culture', sa.Float(), nullable=True),
        sa.Column('rating_compensation', sa.Float(), nullable=True),
        sa.Column('rating_work_life', sa.Float(), nullable=True),
        sa.Column('rating_management', sa.Float(), nullable=True),
        sa.Column('pros', sa.Text(), nullable=True),
        sa.Column('cons', sa.Text(), nullable=True),
        sa.Column('advice', sa.Text(), nullable=True),
        sa.Column('is_current_employee', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('helpful_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create salary_data table
    op.create_table('salary_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_title', sa.String(length=200), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('experience_level', sa.String(length=50), nullable=True),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('salary_currency', sa.String(length=10), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True),
        sa.Column('benefits', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('submitted_by_id', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['submitted_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('salary_data')
    op.drop_table('company_reviews')
    op.drop_table('industry_insights')
    op.drop_table('user_courses')
    op.drop_table('learning_resources')
    op.drop_table('skill_endorsements')
    op.drop_table('career_assessments')
    op.drop_table('mock_interviews')
    op.drop_table('resume_sections')
    op.drop_index(op.f('ix_resumes_share_token'), table_name='resumes')
    op.drop_table('resumes')
    op.drop_table('resume_templates')
