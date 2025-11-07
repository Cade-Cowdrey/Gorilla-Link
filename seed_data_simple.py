"""
Simple data seeding script - directly inserts data without using model relationships
Run this to populate scholarships and jobs
"""
from app_pro import app
from extensions import db
from datetime import datetime, timedelta

def seed_scholarships():
    """Add scholarships using raw SQL"""
    with app.app_context():
        print("\n💰 Adding scholarships...")
        
        # Check if table exists, create if not
        result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='scholarships'"))
        if not result.fetchone():
            print("Creating scholarships table...")
            db.session.execute(db.text("""
                CREATE TABLE scholarships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    amount FLOAT,
                    deadline DATE,
                    eligibility VARCHAR(255),
                    provider VARCHAR(255),
                    url VARCHAR(500),
                    category VARCHAR(100),
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.session.commit()
        
        # Delete existing
        db.session.execute(db.text("DELETE FROM scholarships"))
        
        scholarships_data = [
            ('Presidential Scholarship', 'Full tuition scholarship for incoming freshmen with exceptional academic achievement (3.75+ GPA, 27+ ACT). Renewable for 4 years with 3.5 GPA maintenance.', 10000, (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'), 'Incoming freshmen with 3.75+ GPA and 27+ ACT', 'Pittsburg State University', 'https://www.pittstate.edu/admissions/scholarships.html', 'Academic Excellence', True),
            ('Gorilla Gold Scholarship', 'Merit-based scholarship for high-achieving students. Covers up to $7,500 per year. Based on academic performance, leadership, and community service.', 7500, (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d'), 'Students with 3.5+ GPA and demonstrated leadership', 'Pittsburg State University', 'https://www.pittstate.edu/admissions/scholarships.html', 'Academic Excellence', True),
            ('Crimson Achievement Award', 'Renewable scholarship for students maintaining strong academic performance. Awards range from $2,000-$5,000 annually.', 3500, (datetime.now() + timedelta(days=150)).strftime('%Y-%m-%d'), 'Current students with 3.0+ GPA', 'Pittsburg State University', 'https://www.pittstate.edu/admissions/scholarships.html', 'Academic Excellence', True),
            ('STEM Excellence Award', 'For students pursuing degrees in Science, Technology, Engineering, or Mathematics. Includes mentorship opportunities with faculty and research assistantships.', 5000, (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'), 'STEM majors with 3.25+ GPA', 'Pittsburg State University Foundation', 'https://www.pittstate.edu/academics/stem-scholarships.html', 'STEM', True),
            ('Women in Technology Scholarship', 'Supporting women pursuing computer science, information technology, or engineering degrees. Includes conference funding and networking opportunities.', 3000, (datetime.now() + timedelta(days=75)).strftime('%Y-%m-%d'), 'Female students in CS, IT, or Engineering programs', 'PSU Technology Department', 'https://www.pittstate.edu/technology/scholarships.html', 'STEM', True),
            ('Kelce Business Scholarship', 'For outstanding business students in the Kelce College of Business. Covers tuition and provides internship placement assistance.', 4500, (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'), 'Business majors with 3.2+ GPA', 'Kelce College of Business', 'https://www.pittstate.edu/business/scholarships.html', 'Business', True),
            ('Entrepreneurship Innovation Grant', 'Seed funding for student entrepreneurs developing business ideas. Includes mentorship from local business leaders and startup resources.', 2500, (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'), 'Any major with viable business plan', 'PSU Entrepreneurship Center', 'https://www.pittstate.edu/business/entrepreneurship.html', 'Business', True),
            ('Future Teachers Scholarship', 'For students pursuing teaching certification. Requires commitment to teach in Kansas schools for 3 years after graduation.', 6000, (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d'), 'Education majors with 3.0+ GPA', 'Kansas Board of Education', 'https://www.pittstate.edu/education/scholarships.html', 'Education', True),
            ('Healthcare Heroes Scholarship', 'For nursing and healthcare administration students. Preference given to students from rural Kansas communities.', 5500, (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'), 'Nursing or Healthcare majors', 'Via Christi Hospital Partnership', 'https://www.pittstate.edu/nursing/scholarships.html', 'Healthcare', True),
            ('Rural Health Initiative Grant', 'Supporting students committed to serving rural communities. Includes clinical placement assistance in rural healthcare facilities.', 4000, (datetime.now() + timedelta(days=100)).strftime('%Y-%m-%d'), 'Healthcare students planning rural practice', 'Kansas Rural Health Association', 'https://www.pittstate.edu/nursing/rural-health.html', 'Healthcare', True),
            ('First Generation Student Award', 'For students who are the first in their family to attend college. Includes academic advising, tutoring, and peer mentorship.', 3500, (datetime.now() + timedelta(days=75)).strftime('%Y-%m-%d'), 'First-generation college students', 'PSU Student Success Center', 'https://www.pittstate.edu/student-success/scholarships.html', 'Need-Based', True),
            ('Diversity & Inclusion Scholarship', 'Supporting underrepresented students at PSU. Promotes campus diversity and cultural awareness.', 4000, (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'), 'Underrepresented minority students', 'PSU Office of Diversity', 'https://www.pittstate.edu/diversity/scholarships.html', 'Diversity', True),
            ('Community Leadership Grant', 'Recognizing students with outstanding community service records. Minimum 100 volunteer hours required.', 2500, (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'), 'Students with 100+ volunteer hours', 'PSU Community Engagement Office', 'https://www.pittstate.edu/community/scholarships.html', 'Leadership', True),
            ('Gorilla Athletics Scholarship', 'Athletic scholarships for student-athletes competing in NCAA Division II sports. Combines athletic and academic achievement.', 8000, (datetime.now() + timedelta(days=200)).strftime('%Y-%m-%d'), 'Student-athletes with 2.5+ GPA', 'PSU Athletics Department', 'https://pittstategorillas.com/scholarships', 'Athletics', True),
            ('Jack Kent Cooke Foundation Scholarship', 'Prestigious national scholarship for high-achieving students with financial need. Up to $55,000 per year.', 40000, (datetime.now() + timedelta(days=150)).strftime('%Y-%m-%d'), 'GPA 3.5+, demonstrated financial need', 'Jack Kent Cooke Foundation', 'https://www.jkcf.org/our-scholarships/', 'National', True),
            ('Coca-Cola Scholars Program', 'Achievement-based scholarship recognizing leadership and service. 150 scholarships awarded nationally.', 20000, (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d'), 'High school seniors or current undergraduates', 'Coca-Cola Foundation', 'https://www.coca-colascholarsfoundation.org/', 'National', True),
        ]
        
        sql = """
        INSERT INTO scholarships 
        (title, description, amount, deadline, eligibility, provider, url, category, is_active, created_at)
        VALUES 
        (:title, :description, :amount, :deadline, :eligibility, :provider, :url, :category, :is_active, :created_at)
        """
        
        for s in scholarships_data:
            db.session.execute(db.text(sql), {
                'title': s[0],
                'description': s[1],
                'amount': s[2],
                'deadline': s[3],
                'eligibility': s[4],
                'provider': s[5],
                'url': s[6],
                'category': s[7],
                'is_active': s[8],
                'created_at': datetime.now()
            })
        
        db.session.commit()
        print(f"✅ Added {len(scholarships_data)} scholarships")

def seed_jobs():
    """Add jobs using raw SQL"""
    with app.app_context():
        print("\n💼 Adding jobs...")
        
        # Check if table exists, create if not
        result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"))
        if not result.fetchone():
            print("Creating jobs table...")
            db.session.execute(db.text("""
                CREATE TABLE jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(255) NOT NULL,
                    company VARCHAR(255),
                    location VARCHAR(255),
                    description TEXT,
                    experience_level VARCHAR(50) DEFAULT 'entry',
                    salary_min INTEGER,
                    salary_max INTEGER,
                    years_experience_required VARCHAR(20),
                    is_active BOOLEAN DEFAULT 1,
                    posted_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.session.commit()
        
        # Delete existing
        db.session.execute(db.text("DELETE FROM jobs"))
        
        jobs_data = [
            ('Junior Software Developer', 'Garmin International', 'Olathe, KS', 'Join our innovative team developing GPS navigation and wearable technology. Work on consumer electronics used by millions worldwide. Training provided for new graduates.', 'entry', 65000, 75000, '0-1', True),
            ('IT Support Specialist', 'Sprint (T-Mobile)', 'Overland Park, KS', 'Provide technical support for telecommunications infrastructure. Great benefits and career growth opportunities in Fortune 500 company.', 'entry', 50000, 60000, '0-1', True),
            ('Data Analyst', 'Cerner (Oracle Health)', 'Kansas City, MO', 'Analyze healthcare data to improve patient outcomes. Work with cutting-edge medical technology and big data systems.', 'entry', 60000, 70000, '0-1', True),
            ('Web Developer', 'Commerce Bank', 'Kansas City, MO', 'Develop responsive web applications for online banking. Modern tech stack including React and Node.js.', 'entry', 58000, 68000, '0-1', True),
            ('Financial Analyst', 'Koch Industries', 'Wichita, KS', 'Analyze financial data and support strategic decision-making for one of America\'s largest private companies.', 'entry', 62000, 72000, '0-1', True),
            ('Marketing Coordinator', 'Hallmark Cards', 'Kansas City, MO', 'Support marketing campaigns for iconic greeting card brand. Creative environment with excellent benefits.', 'entry', 48000, 56000, '0-1', True),
            ('Human Resources Assistant', 'Burns & McDonnell', 'Kansas City, MO', 'Support HR operations for global engineering firm. Career growth into HR management roles.', 'entry', 45000, 52000, '0-1', True),
            ('Registered Nurse', 'Via Christi Hospital', 'Pittsburg, KS', 'Provide compassionate care in local community hospital. Multiple specialty areas available. Sign-on bonus offered.', 'entry', 58000, 68000, '0-1', True),
            ('Physical Therapy Assistant', 'NovaCare Rehabilitation', 'Joplin, MO', 'Work alongside licensed physical therapists helping patients recover from injuries and surgeries.', 'entry', 48000, 55000, '0-1', True),
            ('Elementary Teacher', 'Pittsburg USD 250', 'Pittsburg, KS', 'Shape young minds in local school district. Competitive salary with Kansas pension benefits.', 'entry', 42000, 48000, '0-1', True),
            ('High School Math Teacher', 'Blue Valley School District', 'Overland Park, KS', 'Teach mathematics in one of Kansas\' top-rated school districts. Excellent benefits and professional development.', 'entry', 47000, 54000, '0-1', True),
            ('Senior Software Engineer', 'Garmin International', 'Olathe, KS', 'Lead development projects for GPS and aviation systems. Mentor junior developers and drive technical strategy.', 'mid', 95000, 115000, '3-5', True),
            ('Project Manager', 'Black & Veatch', 'Kansas City, MO', 'Manage infrastructure and energy projects. Global travel opportunities and competitive compensation.', 'mid', 85000, 105000, '3-5', True),
            ('Marketing Manager', 'Sprint Center', 'Kansas City, MO', 'Lead marketing initiatives for major sports and entertainment venue. Fast-paced, exciting environment.', 'mid', 75000, 90000, '3-5', True),
            ('Manufacturing Engineer', 'Westar Energy (Evergy)', 'Pittsburg, KS', 'Optimize power generation processes at local energy facility. Competitive salary with excellent benefits.', 'entry', 68000, 78000, '0-1', True),
            ('Quality Assurance Engineer', 'Plastikon Industries', 'Pittsburg, KS', 'Ensure product quality in medical device manufacturing. Local employer with stability and growth.', 'entry', 55000, 65000, '0-1', True),
            ('City Planner', 'City of Kansas City', 'Kansas City, MO', 'Shape urban development and community growth. Excellent government benefits and pension.', 'mid', 62000, 75000, '1-3', True),
            ('Social Worker', 'Kansas Department for Children and Families', 'Pittsburg, KS', 'Make a difference helping families and children in need. Public service loan forgiveness eligible.', 'entry', 45000, 52000, '0-1', True),
            ('Software Development Intern', 'Cerner (Oracle Health)', 'Kansas City, MO', 'Summer internship developing healthcare software. Excellent pathway to full-time employment.', 'entry', 22, 28, '0-1', True),
            ('Business Analytics Intern', 'AMC Theatres', 'Leawood, KS', 'Analyze movie industry data and consumer trends. Hands-on experience with Fortune 500 company.', 'entry', 18, 24, '0-1', True),
        ]
        
        sql = """
        INSERT INTO jobs 
        (title, company, location, description, experience_level, salary_min, salary_max, years_experience_required, is_active, posted_at)
        VALUES 
        (:title, :company, :location, :description, :experience_level, :salary_min, :salary_max, :years_experience_required, :is_active, :posted_at)
        """
        
        for j in jobs_data:
            db.session.execute(db.text(sql), {
                'title': j[0],
                'company': j[1],
                'location': j[2],
                'description': j[3],
                'experience_level': j[4],
                'salary_min': j[5],
                'salary_max': j[6],
                'years_experience_required': j[7],
                'is_active': j[8],
                'posted_at': datetime.now()
            })
        
        db.session.commit()
        print(f"✅ Added {len(jobs_data)} jobs")

def main():
    """Main execution"""
    print("=" * 60)
    print("🎓 Populating Careers & Scholarships Data")
    print("=" * 60)
    
    seed_scholarships()
    seed_jobs()
    
    print("\n" + "=" * 60)
    print("✅ Database populated successfully!")
    print("=" * 60)
    print("\n📊 Summary:")
    with app.app_context():
        result_s = db.session.execute(db.text("SELECT COUNT(*) FROM scholarships")).scalar()
        result_j = db.session.execute(db.text("SELECT COUNT(*) FROM jobs")).scalar()
        print(f"   💰 Scholarships: {result_s}")
        print(f"   💼 Jobs: {result_j}")
    print("\n🚀 You can now view these at:")
    print("   • http://localhost:5000/scholarships")
    print("   • http://localhost:5000/careers")

if __name__ == '__main__':
    main()
