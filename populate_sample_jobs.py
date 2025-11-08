"""
Populate sample jobs for the careers page
"""
from app_pro import app
from extensions import db
from models import Job
from datetime import datetime, timedelta
import random

def populate_jobs():
    with app.app_context():
        # Clear existing sample jobs
        Job.query.delete()
        
        sample_jobs = [
            {
                "title": "Software Engineer",
                "company": "Tech Solutions Inc",
                "location": "Pittsburg, KS",
                "experience_level": "entry",
                "years_experience_required": "0-1",
                "salary_min": 65000,
                "salary_max": 85000,
                "description": "Join our team as a Software Engineer. Work on cutting-edge projects with modern technologies.\n\nRequirements:\n• Bachelor's degree in Computer Science or related field\n• Proficiency in Python, JavaScript, or Java\n• Strong problem-solving skills",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=2)
            },
            {
                "title": "Marketing Coordinator",
                "company": "Creative Agency LLC",
                "location": "Kansas City, MO",
                "experience_level": "entry",
                "years_experience_required": "1-3",
                "salary_min": 45000,
                "salary_max": 55000,
                "description": "Seeking a creative Marketing Coordinator to develop and execute marketing campaigns.\n\nRequirements:\n• Bachelor's degree in Marketing or related field\n• Experience with social media management\n• Excellent communication skills",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=5)
            },
            {
                "title": "Data Analyst",
                "company": "Analytics Corp",
                "location": "Remote",
                "experience_level": "mid",
                "years_experience_required": "3-5",
                "salary_min": 70000,
                "salary_max": 90000,
                "description": "Analyze complex datasets and provide actionable insights to drive business decisions.\n\nRequirements:\n• 3+ years of data analysis experience\n• Proficiency in SQL, Python, and Tableau\n• Strong analytical and problem-solving skills",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=1)
            },
            {
                "title": "Project Manager",
                "company": "Construction Partners",
                "location": "Joplin, MO",
                "experience_level": "mid",
                "years_experience_required": "5-10",
                "salary_min": 75000,
                "salary_max": 95000,
                "description": "Lead construction projects from planning to completion, ensuring quality and timeliness.\n\nRequirements:\n• 5+ years of project management experience\n• PMP certification preferred\n• Excellent leadership and communication skills",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=7)
            },
            {
                "title": "Graphic Designer",
                "company": "Design Studio",
                "location": "Pittsburg, KS",
                "experience_level": "entry",
                "years_experience_required": "0-1",
                "salary_min": 35000,
                "salary_max": 45000,
                "description": "Create visual concepts and designs for various marketing materials and digital platforms.\n\nRequirements:\n• Portfolio demonstrating design skills\n• Proficiency in Adobe Creative Suite\n• Creativity and attention to detail",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=3)
            },
            {
                "title": "Sales Representative",
                "company": "Business Solutions Co",
                "location": "Springfield, MO",
                "experience_level": "entry",
                "years_experience_required": "1-3",
                "salary_min": 40000,
                "salary_max": 60000,
                "description": "Build relationships with clients and drive sales growth in the B2B sector.\n\nRequirements:\n• Bachelor's degree preferred\n• Excellent interpersonal skills\n• Self-motivated and goal-oriented",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=4)
            },
            {
                "title": "Financial Analyst",
                "company": "Finance Group",
                "location": "Remote",
                "experience_level": "mid",
                "years_experience_required": "3-5",
                "salary_min": 65000,
                "salary_max": 85000,
                "description": "Analyze financial data, create models, and provide recommendations to senior management.\n\nRequirements:\n• Bachelor's degree in Finance or Accounting\n• 3+ years of financial analysis experience\n• Advanced Excel skills",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=6)
            },
            {
                "title": "Human Resources Specialist",
                "company": "People First Inc",
                "location": "Pittsburg, KS",
                "experience_level": "entry",
                "years_experience_required": "1-3",
                "salary_min": 45000,
                "salary_max": 55000,
                "description": "Support HR operations including recruitment, onboarding, and employee relations.\n\nRequirements:\n• Bachelor's degree in HR or related field\n• Strong organizational skills\n• Excellent communication abilities",
                "is_active": True,
                "posted_at": datetime.now() - timedelta(days=8)
            }
        ]
        
        for job_data in sample_jobs:
            job = Job(**job_data)
            db.session.add(job)
        
        db.session.commit()
        print(f"[SUCCESS] Successfully added {len(sample_jobs)} sample jobs!")
        
        # Verify
        total = Job.query.count()
        active = Job.query.filter_by(is_active=True).count()
        print(f"[INFO] Total jobs in database: {total}")
        print(f"[INFO] Active jobs: {active}")

if __name__ == "__main__":
    populate_jobs()
