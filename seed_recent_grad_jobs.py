"""
Seed database with recent graduate job opportunities
Shows career progression from entry to mid-level positions
"""
from app_pro import app, db
from models import Job

def seed_recent_grad_jobs():
    """Add sample jobs targeting recent graduates (1-5 years out)"""
    
    recent_grad_jobs = [
        # Entry to Mid-Level Transition Jobs (1-3 years)
        {
            'title': 'Junior Data Analyst',
            'company': 'TechCorp Solutions',
            'location': 'Kansas City, MO',
            'description': 'Growing tech company seeking recent grad with 1-2 years experience in data analysis. Learn advanced analytics and visualization tools.',
            'experience_level': 'mid',
            'years_experience_required': '1-3',
            'salary_min': 52000,
            'salary_max': 62000,
            'is_active': True
        },
        {
            'title': 'Marketing Coordinator',
            'company': 'Midwest Marketing Group',
            'location': 'Overland Park, KS',
            'description': 'Digital marketing role for creative professionals. 1-3 years experience. Manage social media, email campaigns, and analytics.',
            'experience_level': 'mid',
            'years_experience_required': '1-3',
            'salary_min': 48000,
            'salary_max': 58000,
            'is_active': True
        },
        {
            'title': 'Associate Project Manager',
            'company': 'BuildRight Construction',
            'location': 'Wichita, KS',
            'description': 'Construction PM role with mentorship from senior managers. 2-3 years experience preferred. Great growth opportunity.',
            'experience_level': 'mid',
            'years_experience_required': '1-3',
            'salary_min': 55000,
            'salary_max': 65000,
            'is_active': True
        },
        {
            'title': 'Software Developer II',
            'company': 'Innovate Software Inc',
            'location': 'Remote',
            'description': 'Mid-level developer position. 2-4 years coding experience. Work on exciting projects with modern tech stack.',
            'experience_level': 'mid',
            'years_experience_required': '1-3',
            'salary_min': 68000,
            'salary_max': 82000,
            'is_active': True
        },
        {
            'title': 'Account Executive',
            'company': 'Enterprise Sales Co',
            'location': 'Topeka, KS',
            'description': 'B2B sales role for driven professionals. 1-3 years sales experience. Uncapped commission potential.',
            'experience_level': 'mid',
            'years_experience_required': '1-3',
            'salary_min': 50000,
            'salary_max': 75000,
            'is_active': True
        },
        
        # Mid-Level Positions (3-5 years)
        {
            'title': 'Senior Financial Analyst',
            'company': 'Regional Bank of Kansas',
            'location': 'Pittsburg, KS',
            'description': 'Lead financial analysis projects. 3-5 years experience in finance. CFA preferred but not required.',
            'experience_level': 'mid',
            'years_experience_required': '3-5',
            'salary_min': 65000,
            'salary_max': 78000,
            'is_active': True
        },
        {
            'title': 'Operations Manager',
            'company': 'Manufacturing Excellence LLC',
            'location': 'Joplin, MO',
            'description': 'Manage daily operations and team of 15. 4-5 years experience in manufacturing or operations.',
            'experience_level': 'mid',
            'years_experience_required': '3-5',
            'salary_min': 60000,
            'salary_max': 72000,
            'is_active': True
        },
        {
            'title': 'UX/UI Designer',
            'company': 'Creative Digital Agency',
            'location': 'Remote',
            'description': 'Design beautiful user experiences. 3-5 years experience. Portfolio required. Remote-friendly.',
            'experience_level': 'mid',
            'years_experience_required': '3-5',
            'salary_min': 62000,
            'salary_max': 75000,
            'is_active': True
        },
        {
            'title': 'Nursing Supervisor',
            'company': 'Mercy Hospital Joplin',
            'location': 'Joplin, MO',
            'description': 'Lead nursing team in medical-surgical unit. 3-5 years RN experience. BSN preferred.',
            'experience_level': 'mid',
            'years_experience_required': '3-5',
            'salary_min': 58000,
            'salary_max': 68000,
            'is_active': True
        },
        {
            'title': 'Product Manager',
            'company': 'SaaS Startup KC',
            'location': 'Kansas City, MO',
            'description': 'Own product roadmap for B2B SaaS. 3-5 years product experience. Equity included.',
            'experience_level': 'mid',
            'years_experience_required': '3-5',
            'salary_min': 75000,
            'salary_max': 90000,
            'is_active': True
        },
        
        # High-Paying Entry Positions (Career Starters)
        {
            'title': 'Junior Software Engineer',
            'company': 'Tech Innovators',
            'location': 'Remote',
            'description': 'Entry-level coding role with mentorship. Computer Science degree or bootcamp grad. 0-2 years experience.',
            'experience_level': 'entry',
            'years_experience_required': '0-1',
            'salary_min': 55000,
            'salary_max': 65000,
            'is_active': True
        },
        {
            'title': 'Graduate Accountant',
            'company': 'Regional CPA Firm',
            'location': 'Pittsburg, KS',
            'description': 'Recent accounting grads welcome. CPA track. 0-1 years experience. Study support provided.',
            'experience_level': 'entry',
            'years_experience_required': '0-1',
            'salary_min': 48000,
            'salary_max': 54000,
            'is_active': True
        },
    ]
    
    with app.app_context():
        print("🚀 Seeding recent graduate job opportunities...")
        
        for job_data in recent_grad_jobs:
            # Check if job already exists
            existing = Job.query.filter_by(
                title=job_data['title'],
                company=job_data['company']
            ).first()
            
            if not existing:
                job = Job(**job_data)
                db.session.add(job)
                print(f"  ✓ Added: {job_data['title']} at {job_data['company']} (${job_data['salary_min']:,}-${job_data['salary_max']:,})")
        
        db.session.commit()
        print(f"\n✅ Successfully seeded {len(recent_grad_jobs)} recent graduate jobs!")
        print("\n📊 Salary Ranges:")
        print("   Entry (0-1 years): $48K-$65K")
        print("   Mid (1-3 years): $48K-$82K")
        print("   Mid (3-5 years): $58K-$90K")

if __name__ == "__main__":
    seed_recent_grad_jobs()
