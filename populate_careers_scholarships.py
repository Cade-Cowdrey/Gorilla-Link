"""
Populate database with real careers and scholarships data
Run this script to add realistic data for students
"""
from app_pro import app
from extensions import db
from models import Job, Scholarship
from datetime import datetime, timedelta
import random

def clear_existing_data():
    """Clear existing jobs and scholarships"""
    with app.app_context():
        print("🗑️  Clearing existing data...")
        Job.query.delete()
        Scholarship.query.delete()
        db.session.commit()
        print("✅ Existing data cleared")

def populate_scholarships():
    """Add real scholarships for Pitt State students"""
    with app.app_context():
        print("\n💰 Adding scholarships...")
        
        scholarships = [
            # Pitt State Specific
            {
                'title': 'Presidential Scholarship',
                'description': 'Full tuition scholarship for incoming freshmen with exceptional academic achievement (3.75+ GPA, 27+ ACT). Renewable for 4 years with 3.5 GPA maintenance.',
                'amount': 10000,
                'deadline': datetime.now().date() + timedelta(days=180),
                'eligibility': 'Incoming freshmen with 3.75+ GPA and 27+ ACT',
                'provider': 'Pittsburg State University',
                'url': 'https://www.pittstate.edu/admissions/scholarships.html',
                'category': 'Academic Excellence',
                'is_active': True
            },
            {
                'title': 'Gorilla Gold Scholarship',
                'description': 'Merit-based scholarship for high-achieving students. Covers up to $7,500 per year. Based on academic performance, leadership, and community service.',
                'amount': 7500,
                'deadline': datetime.now().date() + timedelta(days=120),
                'eligibility': 'Students with 3.5+ GPA and demonstrated leadership',
                'provider': 'Pittsburg State University',
                'url': 'https://www.pittstate.edu/admissions/scholarships.html',
                'category': 'Academic Excellence',
                'is_active': True
            },
            {
                'title': 'Crimson Achievement Award',
                'description': 'Renewable scholarship for students maintaining strong academic performance. Awards range from $2,000-$5,000 annually.',
                'amount': 3500,
                'deadline': datetime.now().date() + timedelta(days=150),
                'eligibility': 'Current students with 3.0+ GPA',
                'provider': 'Pittsburg State University',
                'url': 'https://www.pittstate.edu/admissions/scholarships.html',
                'category': 'Academic Excellence',
                'is_active': True
            },
            
            # STEM Scholarships
            {
                'title': 'STEM Excellence Award',
                'description': 'For students pursuing degrees in Science, Technology, Engineering, or Mathematics. Includes mentorship opportunities with faculty and research assistantships.',
                'amount': 5000,
                'deadline': datetime.now().date() + timedelta(days=90),
                'eligibility': 'STEM majors with 3.25+ GPA',
                'provider': 'Pittsburg State University Foundation',
                'url': 'https://www.pittstate.edu/academics/stem-scholarships.html',
                'category': 'STEM',
                'is_active': True
            },
            {
                'title': 'Women in Technology Scholarship',
                'description': 'Supporting women pursuing computer science, information technology, or engineering degrees. Includes conference funding and networking opportunities.',
                'amount': 3000,
                'deadline': datetime.now().date() + timedelta(days=75),
                'eligibility': 'Female students in CS, IT, or Engineering programs',
                'provider': 'PSU Technology Department',
                'url': 'https://www.pittstate.edu/technology/scholarships.html',
                'category': 'STEM',
                'is_active': True
            },
            
            # Business & Economics
            {
                'title': 'Kelce Business Scholarship',
                'description': 'For outstanding business students in the Kelce College of Business. Covers tuition and provides internship placement assistance.',
                'amount': 4500,
                'deadline': datetime.now().date() + timedelta(days=60),
                'eligibility': 'Business majors with 3.2+ GPA',
                'provider': 'Kelce College of Business',
                'url': 'https://www.pittstate.edu/business/scholarships.html',
                'category': 'Business',
                'is_active': True
            },
            {
                'title': 'Entrepreneurship Innovation Grant',
                'description': 'Seed funding for student entrepreneurs developing business ideas. Includes mentorship from local business leaders and startup resources.',
                'amount': 2500,
                'deadline': datetime.now().date() + timedelta(days=45),
                'eligibility': 'Any major with viable business plan',
                'provider': 'PSU Entrepreneurship Center',
                'url': 'https://www.pittstate.edu/business/entrepreneurship.html',
                'category': 'Business',
                'is_active': True
            },
            
            # Education
            {
                'title': 'Future Teachers Scholarship',
                'description': 'For students pursuing teaching certification. Requires commitment to teach in Kansas schools for 3 years after graduation.',
                'amount': 6000,
                'deadline': datetime.now().date() + timedelta(days=120),
                'eligibility': 'Education majors with 3.0+ GPA',
                'provider': 'Kansas Board of Education',
                'url': 'https://www.pittstate.edu/education/scholarships.html',
                'category': 'Education',
                'is_active': True
            },
            
            # Healthcare & Nursing
            {
                'title': 'Healthcare Heroes Scholarship',
                'description': 'For nursing and healthcare administration students. Preference given to students from rural Kansas communities.',
                'amount': 5500,
                'deadline': datetime.now().date() + timedelta(days=90),
                'eligibility': 'Nursing or Healthcare majors',
                'provider': 'Via Christi Hospital Partnership',
                'url': 'https://www.pittstate.edu/nursing/scholarships.html',
                'category': 'Healthcare',
                'is_active': True
            },
            {
                'title': 'Rural Health Initiative Grant',
                'description': 'Supporting students committed to serving rural communities. Includes clinical placement assistance in rural healthcare facilities.',
                'amount': 4000,
                'deadline': datetime.now().date() + timedelta(days=100),
                'eligibility': 'Healthcare students planning rural practice',
                'provider': 'Kansas Rural Health Association',
                'url': 'https://www.pittstate.edu/nursing/rural-health.html',
                'category': 'Healthcare',
                'is_active': True
            },
            
            # Need-Based & Diversity
            {
                'title': 'First Generation Student Award',
                'description': 'For students who are the first in their family to attend college. Includes academic advising, tutoring, and peer mentorship.',
                'amount': 3500,
                'deadline': datetime.now().date() + timedelta(days=75),
                'eligibility': 'First-generation college students',
                'provider': 'PSU Student Success Center',
                'url': 'https://www.pittstate.edu/student-success/scholarships.html',
                'category': 'Need-Based',
                'is_active': True
            },
            {
                'title': 'Diversity & Inclusion Scholarship',
                'description': 'Supporting underrepresented students at PSU. Promotes campus diversity and cultural awareness.',
                'amount': 4000,
                'deadline': datetime.now().date() + timedelta(days=90),
                'eligibility': 'Underrepresented minority students',
                'provider': 'PSU Office of Diversity',
                'url': 'https://www.pittstate.edu/diversity/scholarships.html',
                'category': 'Diversity',
                'is_active': True
            },
            
            # Community Leadership
            {
                'title': 'Community Leadership Grant',
                'description': 'Recognizing students with outstanding community service records. Minimum 100 volunteer hours required.',
                'amount': 2500,
                'deadline': datetime.now().date() + timedelta(days=60),
                'eligibility': 'Students with 100+ volunteer hours',
                'provider': 'PSU Community Engagement Office',
                'url': 'https://www.pittstate.edu/community/scholarships.html',
                'category': 'Leadership',
                'is_active': True
            },
            
            # Athletics
            {
                'title': 'Gorilla Athletics Scholarship',
                'description': 'Athletic scholarships for student-athletes competing in NCAA Division II sports. Combines athletic and academic achievement.',
                'amount': 8000,
                'deadline': datetime.now().date() + timedelta(days=200),
                'eligibility': 'Student-athletes with 2.5+ GPA',
                'provider': 'PSU Athletics Department',
                'url': 'https://pittstategorillas.com/scholarships',
                'category': 'Athletics',
                'is_active': True
            },
            
            # External Scholarships
            {
                'title': 'Jack Kent Cooke Foundation Scholarship',
                'description': 'Prestigious national scholarship for high-achieving students with financial need. Up to $55,000 per year.',
                'amount': 40000,
                'deadline': datetime.now().date() + timedelta(days=150),
                'eligibility': 'GPA 3.5+, demonstrated financial need',
                'provider': 'Jack Kent Cooke Foundation',
                'url': 'https://www.jkcf.org/our-scholarships/',
                'category': 'National',
                'is_active': True
            },
            {
                'title': 'Coca-Cola Scholars Program',
                'description': 'Achievement-based scholarship recognizing leadership and service. 150 scholarships awarded nationally.',
                'amount': 20000,
                'deadline': datetime.now().date() + timedelta(days=120),
                'eligibility': 'High school seniors or current undergraduates',
                'provider': 'Coca-Cola Foundation',
                'url': 'https://www.coca-colascholarsfoundation.org/',
                'category': 'National',
                'is_active': True
            },
        ]
        
        for s_data in scholarships:
            scholarship = Scholarship(**s_data)
            db.session.add(scholarship)
        
        db.session.commit()
        print(f"✅ Added {len(scholarships)} scholarships")

def populate_jobs():
    """Add real job opportunities for Pitt State students and graduates"""
    with app.app_context():
        print("\n💼 Adding jobs...")
        
        jobs = [
            # Entry-Level Tech Jobs
            {
                'title': 'Junior Software Developer',
                'company': 'Garmin International',
                'location': 'Olathe, KS',
                'description': 'Join our innovative team developing GPS navigation and wearable technology. Work on consumer electronics used by millions worldwide. Training provided for new graduates.',
                'experience_level': 'entry',
                'salary_min': 65000,
                'salary_max': 75000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'IT Support Specialist',
                'company': 'Sprint (T-Mobile)',
                'location': 'Overland Park, KS',
                'description': 'Provide technical support for telecommunications infrastructure. Great benefits and career growth opportunities in Fortune 500 company.',
                'experience_level': 'entry',
                'salary_min': 50000,
                'salary_max': 60000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'Data Analyst',
                'company': 'Cerner (Oracle Health)',
                'location': 'Kansas City, MO',
                'description': 'Analyze healthcare data to improve patient outcomes. Work with cutting-edge medical technology and big data systems.',
                'experience_level': 'entry',
                'salary_min': 60000,
                'salary_max': 70000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'Web Developer',
                'company': 'Commerce Bank',
                'location': 'Kansas City, MO',
                'description': 'Develop responsive web applications for online banking. Modern tech stack including React and Node.js.',
                'experience_level': 'entry',
                'salary_min': 58000,
                'salary_max': 68000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            
            # Business & Finance Entry-Level
            {
                'title': 'Financial Analyst',
                'company': 'Koch Industries',
                'location': 'Wichita, KS',
                'description': 'Analyze financial data and support strategic decision-making for one of America\'s largest private companies.',
                'experience_level': 'entry',
                'salary_min': 62000,
                'salary_max': 72000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'Marketing Coordinator',
                'company': 'Hallmark Cards',
                'location': 'Kansas City, MO',
                'description': 'Support marketing campaigns for iconic greeting card brand. Creative environment with excellent benefits.',
                'experience_level': 'entry',
                'salary_min': 48000,
                'salary_max': 56000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'Human Resources Assistant',
                'company': 'Burns & McDonnell',
                'location': 'Kansas City, MO',
                'description': 'Support HR operations for global engineering firm. Career growth into HR management roles.',
                'experience_level': 'entry',
                'salary_min': 45000,
                'salary_max': 52000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            
            # Healthcare Entry-Level
            {
                'title': 'Registered Nurse',
                'company': 'Via Christi Hospital',
                'location': 'Pittsburg, KS',
                'description': 'Provide compassionate care in local community hospital. Multiple specialty areas available. Sign-on bonus offered.',
                'experience_level': 'entry',
                'salary_min': 58000,
                'salary_max': 68000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'Physical Therapy Assistant',
                'company': 'NovaCare Rehabilitation',
                'location': 'Joplin, MO',
                'description': 'Work alongside licensed physical therapists helping patients recover from injuries and surgeries.',
                'experience_level': 'entry',
                'salary_min': 48000,
                'salary_max': 55000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            
            # Education Entry-Level
            {
                'title': 'Elementary Teacher',
                'company': 'Pittsburg USD 250',
                'location': 'Pittsburg, KS',
                'description': 'Shape young minds in local school district. Competitive salary with Kansas pension benefits.',
                'experience_level': 'entry',
                'salary_min': 42000,
                'salary_max': 48000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'High School Math Teacher',
                'company': 'Blue Valley School District',
                'location': 'Overland Park, KS',
                'description': 'Teach mathematics in one of Kansas\' top-rated school districts. Excellent benefits and professional development.',
                'experience_level': 'entry',
                'salary_min': 47000,
                'salary_max': 54000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            
            # Mid-Level Career Growth
            {
                'title': 'Senior Software Engineer',
                'company': 'Garmin International',
                'location': 'Olathe, KS',
                'description': 'Lead development projects for GPS and aviation systems. Mentor junior developers and drive technical strategy.',
                'experience_level': 'mid',
                'salary_min': 95000,
                'salary_max': 115000,
                'years_experience_required': '3-5',
                'is_active': True
            },
            {
                'title': 'Project Manager',
                'company': 'Black & Veatch',
                'location': 'Kansas City, MO',
                'description': 'Manage infrastructure and energy projects. Global travel opportunities and competitive compensation.',
                'experience_level': 'mid',
                'salary_min': 85000,
                'salary_max': 105000,
                'years_experience_required': '3-5',
                'is_active': True
            },
            {
                'title': 'Marketing Manager',
                'company': 'Sprint Center',
                'location': 'Kansas City, MO',
                'description': 'Lead marketing initiatives for major sports and entertainment venue. Fast-paced, exciting environment.',
                'experience_level': 'mid',
                'salary_min': 75000,
                'salary_max': 90000,
                'years_experience_required': '3-5',
                'is_active': True
            },
            
            # Manufacturing & Engineering
            {
                'title': 'Manufacturing Engineer',
                'company': 'Westar Energy (Evergy)',
                'location': 'Pittsburg, KS',
                'description': 'Optimize power generation processes at local energy facility. Competitive salary with excellent benefits.',
                'experience_level': 'entry',
                'salary_min': 68000,
                'salary_max': 78000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'Quality Assurance Engineer',
                'company': 'Plastikon Industries',
                'location': 'Pittsburg, KS',
                'description': 'Ensure product quality in medical device manufacturing. Local employer with stability and growth.',
                'experience_level': 'entry',
                'salary_min': 55000,
                'salary_max': 65000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            
            # Government & Public Service
            {
                'title': 'City Planner',
                'company': 'City of Kansas City',
                'location': 'Kansas City, MO',
                'description': 'Shape urban development and community growth. Excellent government benefits and pension.',
                'experience_level': 'mid',
                'salary_min': 62000,
                'salary_max': 75000,
                'years_experience_required': '1-3',
                'is_active': True
            },
            {
                'title': 'Social Worker',
                'company': 'Kansas Department for Children and Families',
                'location': 'Pittsburg, KS',
                'description': 'Make a difference helping families and children in need. Public service loan forgiveness eligible.',
                'experience_level': 'entry',
                'salary_min': 45000,
                'salary_max': 52000,
                'years_experience_required': '0-1',
                'is_active': True
            },
            
            # Internships & Co-ops
            {
                'title': 'Software Development Intern',
                'company': 'Cerner (Oracle Health)',
                'location': 'Kansas City, MO',
                'description': 'Summer internship developing healthcare software. Excellent pathway to full-time employment.',
                'experience_level': 'entry',
                'salary_min': 22,  # Hourly
                'salary_max': 28,
                'years_experience_required': '0-1',
                'is_active': True
            },
            {
                'title': 'Business Analytics Intern',
                'company': 'AMC Theatres',
                'location': 'Leawood, KS',
                'description': 'Analyze movie industry data and consumer trends. Hands-on experience with Fortune 500 company.',
                'experience_level': 'entry',
                'salary_min': 18,  # Hourly
                'salary_max': 24,
                'years_experience_required': '0-1',
                'is_active': True
            },
        ]
        
        for j_data in jobs:
            job = Job(**j_data)
            db.session.add(job)
        
        db.session.commit()
        print(f"✅ Added {len(jobs)} jobs")

def main():
    """Main execution"""
    print("=" * 60)
    print("🎓 Populating Careers & Scholarships Data")
    print("=" * 60)
    
    # Clear existing
    clear_existing_data()
    
    # Populate new data
    populate_scholarships()
    populate_jobs()
    
    print("\n" + "=" * 60)
    print("✅ Database populated successfully!")
    print("=" * 60)
    print("\n📊 Summary:")
    with app.app_context():
        scholarship_count = Scholarship.query.count()
        job_count = Job.query.count()
        print(f"   💰 Scholarships: {scholarship_count}")
        print(f"   💼 Jobs: {job_count}")
    print("\n🚀 You can now view these at:")
    print("   • /scholarships")
    print("   • /careers")

if __name__ == '__main__':
    main()
