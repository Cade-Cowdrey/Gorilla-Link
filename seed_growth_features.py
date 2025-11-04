"""
Seed Growth Features - Badges, Forum Categories, Sample Data
Run this after migrations to populate the database
"""

from extensions import db
from models_growth_features import (
    Badge, ForumCategory, MentorshipProgram, 
    SuccessStory, UserPoints, UserStreak
)
from models import User
from datetime import datetime


def seed_badges():
    """Create achievement badges"""
    badges = [
        {
            'name': 'Resume Master',
            'description': 'Achieved 90+ ATS score on resume',
            'icon': 'file-alt',
            'points': 50,
            'criteria': {'resume_score': 90}
        },
        {
            'name': 'Super Connector',
            'description': 'Connected with 25+ professionals',
            'icon': 'users',
            'points': 100,
            'criteria': {'connections': 25}
        },
        {
            'name': 'Job Hunter',
            'description': 'Applied to 10+ jobs',
            'icon': 'briefcase',
            'points': 75,
            'criteria': {'applications': 10}
        },
        {
            'name': 'Interview Pro',
            'description': 'Completed 5+ interviews',
            'icon': 'handshake',
            'points': 150,
            'criteria': {'interviews': 5}
        },
        {
            'name': 'Lifelong Learner',
            'description': 'Completed 3+ courses',
            'icon': 'graduation-cap',
            'points': 100,
            'criteria': {'courses': 3}
        },
        {
            'name': 'Skill Validator',
            'description': 'Received 5+ skill endorsements',
            'icon': 'star',
            'points': 50,
            'criteria': {'endorsements': 5}
        },
        {
            'name': 'Career Explorer',
            'description': 'Completed all career assessments',
            'icon': 'compass',
            'points': 75,
            'criteria': {'assessments_complete': True}
        },
        {
            'name': 'Community Helper',
            'description': 'Helped 3+ students as mentor',
            'icon': 'hands-helping',
            'points': 200,
            'criteria': {'mentees': 3}
        },
        {
            'name': '7-Day Streak',
            'description': 'Logged in 7 days in a row',
            'icon': 'fire',
            'points': 50,
            'criteria': {'streak_days': 7}
        },
        {
            'name': '30-Day Streak',
            'description': 'Logged in 30 days in a row',
            'icon': 'fire',
            'points': 200,
            'criteria': {'streak_days': 30}
        },
        {
            'name': 'Profile Complete',
            'description': 'Completed 100% of profile',
            'icon': 'check-circle',
            'points': 100,
            'criteria': {'profile_completion': 100}
        },
        {
            'name': 'Early Adopter',
            'description': 'Joined in the first 100 users',
            'icon': 'rocket',
            'points': 500,
            'criteria': {'user_id': 100}
        },
        {
            'name': 'Referral Champion',
            'description': 'Referred 5+ new users',
            'icon': 'share-alt',
            'points': 250,
            'criteria': {'referrals': 5}
        },
        {
            'name': 'Success Story Teller',
            'description': 'Shared your success story',
            'icon': 'bullhorn',
            'points': 75,
            'criteria': {'shared_story': True}
        },
        {
            'name': 'Forum Contributor',
            'description': 'Posted 10+ helpful forum replies',
            'icon': 'comments',
            'points': 100,
            'criteria': {'forum_posts': 10}
        }
    ]
    
    print("Creating badges...")
    for badge_data in badges:
        existing = Badge.query.filter_by(name=badge_data['name']).first()
        if not existing:
            badge = Badge(**badge_data)
            db.session.add(badge)
            print(f"  ✓ {badge_data['name']}")
    
    db.session.commit()
    print(f"✓ Created {len(badges)} badges\n")


def seed_forum_categories():
    """Create forum categories"""
    categories = [
        {
            'name': 'Career Advice',
            'description': 'Get advice on career planning, job search strategies, and professional development',
            'icon': 'briefcase',
            'display_order': 1
        },
        {
            'name': 'Resume & Interview Help',
            'description': 'Share resumes for feedback, practice interviews, and get tips',
            'icon': 'file-alt',
            'display_order': 2
        },
        {
            'name': 'Job Opportunities',
            'description': 'Share and discuss job openings, internships, and opportunities',
            'icon': 'search',
            'display_order': 3
        },
        {
            'name': 'Networking',
            'description': 'Connect with alumni, find mentors, and build your professional network',
            'icon': 'users',
            'display_order': 4
        },
        {
            'name': 'Industry Discussions',
            'description': 'Discuss trends, news, and insights from various industries',
            'icon': 'industry',
            'display_order': 5
        },
        {
            'name': 'Student Life',
            'description': 'Campus life, courses, professors, and student experiences at PSU',
            'icon': 'university',
            'display_order': 6
        },
        {
            'name': 'Technical Help',
            'description': 'Get help with coding, projects, and technical challenges',
            'icon': 'code',
            'display_order': 7
        },
        {
            'name': 'Announcements',
            'description': 'Official announcements from PSU Career Services and alumni association',
            'icon': 'bullhorn',
            'display_order': 8
        }
    ]
    
    print("Creating forum categories...")
    for cat_data in categories:
        existing = ForumCategory.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = ForumCategory(**cat_data)
            db.session.add(category)
            print(f"  ✓ {cat_data['name']}")
    
    db.session.commit()
    print(f"✓ Created {len(categories)} forum categories\n")


def seed_mentorship_programs():
    """Create mentorship programs"""
    programs = [
        {
            'name': 'General Career Mentorship',
            'description': 'Connect with experienced professionals for general career guidance',
            'duration_weeks': 12,
            'is_active': True
        },
        {
            'name': 'Tech Industry Mentorship',
            'description': 'Get mentored by tech professionals in software, data science, and IT',
            'duration_weeks': 16,
            'is_active': True
        },
        {
            'name': 'Business & Finance Mentorship',
            'description': 'Learn from business leaders and finance professionals',
            'duration_weeks': 12,
            'is_active': True
        },
        {
            'name': 'Education Mentorship',
            'description': 'Connect with experienced educators and administrators',
            'duration_weeks': 10,
            'is_active': True
        },
        {
            'name': 'First-Year Student Program',
            'description': 'Upper-class students mentor freshmen through their first year',
            'duration_weeks': 36,
            'is_active': True
        }
    ]
    
    print("Creating mentorship programs...")
    for prog_data in programs:
        existing = MentorshipProgram.query.filter_by(name=prog_data['name']).first()
        if not existing:
            program = MentorshipProgram(**prog_data)
            db.session.add(program)
            print(f"  ✓ {prog_data['name']}")
    
    db.session.commit()
    print(f"✓ Created {len(programs)} mentorship programs\n")


def seed_sample_success_stories():
    """Create sample success stories"""
    # Get first user as author (or create sample user)
    author = User.query.first()
    if not author:
        print("⚠ No users found. Skipping success stories.\n")
        return
    
    stories = [
        {
            'user_id': author.id,
            'story_type': 'job_offer',
            'title': 'Landed Dream Job at Tech Startup!',
            'content': 'After months of searching and using the PSU Connect auto-apply feature, I finally landed my dream job as a Software Engineer at a growing startup in Kansas City. The AI resume builder really helped me tailor my application!',
            'company': 'TechCo Startup',
            'position': 'Software Engineer',
            'salary_range': '$65k-75k',
            'is_featured': True
        },
        {
            'user_id': author.id,
            'story_type': 'internship',
            'title': 'Summer Internship Success',
            'content': 'Got an amazing summer internship opportunity through a connection I made on PSU Connect. The mentorship program really prepared me for the interview process!',
            'company': 'Fortune 500 Company',
            'position': 'Marketing Intern',
            'is_featured': False
        }
    ]
    
    print("Creating sample success stories...")
    for story_data in stories:
        story = SuccessStory(**story_data)
        db.session.add(story)
        print(f"  ✓ {story_data['title']}")
    
    db.session.commit()
    print(f"✓ Created {len(stories)} success stories\n")


def main():
    """Run all seed functions"""
    print("\n" + "="*50)
    print("PSU CONNECT - SEEDING GROWTH FEATURES")
    print("="*50 + "\n")
    
    seed_badges()
    seed_forum_categories()
    seed_mentorship_programs()
    seed_sample_success_stories()
    
    print("="*50)
    print("✓ ALL SEED DATA CREATED SUCCESSFULLY!")
    print("="*50 + "\n")


if __name__ == '__main__':
    from app_pro import app
    with app.app_context():
        main()
