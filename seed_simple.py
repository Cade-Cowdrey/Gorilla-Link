#!/usr/bin/env python3
"""
Simple seed script - Just scholarships and jobs
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and extensions
from flask import Flask
from config.config_production import ConfigProduction
from extensions import db
from models import Scholarship, Job

# Create a minimal app for seeding
app = Flask(__name__)
app.config.from_object(ConfigProduction)
db.init_app(app)

def seed_scholarships():
    """Seed real scholarships"""
    print("\n💰 Seeding Scholarships...")
    
    scholarships = [
        {
            'title': 'National Science Foundation STEM Scholarship',
            'provider': 'National Science Foundation',
            'amount': 10000,
            'deadline': datetime.now() + timedelta(days=90),
            'category': 'STEM',
            'description': 'Scholarship for students pursuing STEM degrees with financial need.',
            'eligibility': 'Must be pursuing a STEM degree with 3.0+ GPA',
            'url': 'https://www.nsf.gov/funding/programs/s-stem',
            'is_active': True
        },
        {
            'title': 'Society of Women Engineers Scholarship',
            'provider': 'Society of Women Engineers',
            'amount': 5000,
            'deadline': datetime.now() + timedelta(days=120),
            'category': 'STEM',
            'description': 'Supporting women in engineering and technology fields.',
            'eligibility': 'Female students in engineering programs',
            'url': 'https://swe.org/scholarships/',
            'is_active': True
        },
        {
            'title': 'Nursing Excellence Scholarship',
            'provider': 'American Nurses Foundation',
            'amount': 3000,
            'deadline': datetime.now() + timedelta(days=60),
            'category': 'Healthcare',
            'description': 'Financial assistance for nursing students.',
            'eligibility': 'Enrolled in accredited nursing program, 3.25+ GPA',
            'url': 'https://www.nursingworld.org/foundation/',
            'is_active': True
        },
        {
            'title': 'Future Business Leaders Scholarship',
            'provider': 'FBLA-PBL',
            'amount': 4000,
            'deadline': datetime.now() + timedelta(days=100),
            'category': 'Business',
            'description': 'Supporting the next generation of business leaders.',
            'eligibility': 'Business majors with leadership experience',
            'url': 'https://www.fbla.org/scholarships/',
            'is_active': True
        },
        {
            'title': 'Pell Grant (Federal)',
            'provider': 'U.S. Department of Education',
            'amount': 6895,
            'deadline': datetime.now() + timedelta(days=365),
            'category': 'General',
            'description': 'Federal grant for undergraduate students with exceptional financial need.',
            'eligibility': 'U.S. citizen with demonstrated financial need',
            'url': 'https://studentaid.gov/understand-aid/types/grants/pell',
            'is_active': True
        },
        {
            'title': 'Jack Kent Cooke Foundation Scholarship',
            'provider': 'Jack Kent Cooke Foundation',
            'amount': 40000,
            'deadline': datetime.now() + timedelta(days=150),
            'category': 'General',
            'description': 'One of the largest scholarships in America.',
            'eligibility': '3.5+ GPA, demonstrated financial need',
            'url': 'https://www.jkcf.org/our-scholarships/',
            'is_active': True
        },
        {
            'title': 'PSU Foundation Scholarship',
            'provider': 'Pittsburg State University Foundation',
            'amount': 3500,
            'deadline': datetime.now() + timedelta(days=60),
            'category': 'General',
            'description': 'Merit-based scholarship for PSU students.',
            'eligibility': 'Current PSU student with 3.0+ GPA',
            'url': 'https://www.pittstate.edu/admission/scholarships/',
            'is_active': True
        },
    ]
    
    count = 0
    for sch_data in scholarships:
        scholarship = Scholarship(**sch_data)
        db.session.add(scholarship)
        count += 1
    
    db.session.commit()
    print(f"   ✅ Added {count} scholarships")


def seed_jobs():
    """Seed career opportunities"""
    print("\n💼 Seeding Career Opportunities...")
    
    jobs = [
        {
            'title': 'Junior Software Developer',
            'company': 'Tech Innovations Inc.',
            'location': 'Kansas City, KS',
            'description': 'Join our development team building cutting-edge web applications.',
            'experience_level': 'entry',
            'salary_min': 55000,
            'salary_max': 70000,
            'years_experience_required': '0-1',
            'is_active': True,
            'posted_at': datetime.now() - timedelta(days=5)
        },
        {
            'title': 'IT Support Specialist',
            'company': 'Midwest Solutions',
            'location': 'Overland Park, KS',
            'description': 'Provide technical support to end users.',
            'experience_level': 'entry',
            'salary_min': 42000,
            'salary_max': 52000,
            'years_experience_required': '0-1',
            'is_active': True,
            'posted_at': datetime.now() - timedelta(days=3)
        },
        {
            'title': 'Registered Nurse - Med/Surg',
            'company': 'Via Christi Hospital',
            'location': 'Pittsburg, KS',
            'description': 'RN position in medical-surgical unit. Sign-on bonus available.',
            'experience_level': 'entry',
            'salary_min': 58000,
            'salary_max': 72000,
            'years_experience_required': '0-1',
            'is_active': True,
            'posted_at': datetime.now() - timedelta(days=2)
        },
        {
            'title': 'Financial Analyst',
            'company': 'Commerce Bank',
            'location': 'Kansas City, MO',
            'description': 'Analyze financial data and support business decisions.',
            'experience_level': 'entry',
            'salary_min': 52000,
            'salary_max': 65000,
            'years_experience_required': '1-3',
            'is_active': True,
            'posted_at': datetime.now() - timedelta(days=4)
        },
        {
            'title': 'Marketing Coordinator',
            'company': 'Brand Builders LLC',
            'location': 'Olathe, KS',
            'description': 'Support marketing campaigns and social media management.',
            'experience_level': 'entry',
            'salary_min': 40000,
            'salary_max': 50000,
            'years_experience_required': '0-1',
            'is_active': True,
            'posted_at': datetime.now() - timedelta(days=8)
        },
        {
            'title': 'Senior Software Engineer',
            'company': 'Cloud Systems Inc.',
            'location': 'Kansas City, KS',
            'description': 'Lead development of cloud-based solutions.',
            'experience_level': 'mid',
            'salary_min': 85000,
            'salary_max': 115000,
            'years_experience_required': '3-5',
            'is_active': True,
            'posted_at': datetime.now() - timedelta(days=10)
        },
    ]
    
    count = 0
    for job_data in jobs:
        job = Job(**job_data)
        db.session.add(job)
        count += 1
    
    db.session.commit()
    print(f"   ✅ Added {count} career opportunities")


def main():
    """Main seed function"""
    print("=" * 60)
    print("🦍 PittState Connect - Simple Database Seed")
    print("=" * 60)
    
    with app.app_context():
        # Create all tables
        print("\n🔨 Creating database tables...")
        db.create_all()
        print("   ✅ Tables created")
        
        # Clear existing data (if any)
        print("\n🧹 Clearing existing scholarships and jobs...")
        try:
            Scholarship.query.delete()
            Job.query.delete()
            db.session.commit()
            print("   ✅ Cleared")
        except Exception as e:
            print(f"   ⚠️  No existing data to clear: {e}")
            db.session.rollback()
        
        # Seed data
        seed_scholarships()
        seed_jobs()
        
        print("\n" + "=" * 60)
        print("✅ Database seeding complete!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   Scholarships: {Scholarship.query.count()}")
        print(f"   Jobs: {Job.query.count()}")
        print("\n🎉 Your app is now demo-ready!")


if __name__ == "__main__":
    main()
