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
            # REAL National Scholarships - Students Can Apply!
            ('Jack Kent Cooke Foundation Undergraduate Transfer Scholarship', 'Prestigious scholarship for community college students transferring to 4-year institutions. Covers up to $55,000 per year for tuition, books, and living expenses. Highly competitive - only 85 awards nationally.', 55000, '2025-12-02', 'Community college students with 3.5+ GPA transferring to 4-year college', 'Jack Kent Cooke Foundation', 'https://www.jkcf.org/our-scholarships/undergraduate-transfer-scholarship/', 'National', True),
            ('Coca-Cola Scholars Program', 'One of the most prestigious scholarships in America. $20,000 award recognizing students who demonstrate leadership, service, and academic achievement. 150 scholarships awarded annually.', 20000, '2025-10-31', 'High school seniors with 3.0+ GPA, demonstrated leadership and community service', 'Coca-Cola Scholars Foundation', 'https://www.coca-colascholarsfoundation.org/apply/', 'National', True),
            ('Dell Scholars Program', 'Designed for students who have overcome significant obstacles. $20,000 scholarship plus laptop, textbook credits, and ongoing support. Must be participating in college readiness program.', 20000, '2025-12-01', 'High school seniors with 2.4+ GPA, financial need, college readiness program participant', 'Michael & Susan Dell Foundation', 'https://www.dellscholars.org/scholarship/eligibility/', 'National', True),
            ('Gates Scholarship', 'Full ride scholarship covering full cost of attendance not covered by financial aid. For high-achieving minority students with significant financial need. 300 scholarships annually.', 50000, '2025-09-15', 'Pell-eligible minority high school seniors with 3.3+ GPA', 'Gates Foundation', 'https://www.thegatesscholarship.org/scholarship', 'National', True),
            ('Burger King Scholars Program', 'For students working part-time while maintaining strong academics. Awards range from $1,000 to $50,000. Over $7 million awarded annually to students across North America.', 5000, '2025-12-15', 'High school seniors or undergrads with 2.5+ GPA, work experience, community service', 'Burger King Foundation', 'https://www.burgerkingfoundation.org/our-scholarships', 'National', True),
            
            # STEM Scholarships
            ('Google Lime Scholarship', 'For computer science students with disabilities. $10,000 for undergraduate or $5,000 for graduate students. Includes invitation to Google Scholars Retreat.', 10000, '2025-12-06', 'CS/Computer Engineering majors with visible or invisible disability, 3.0+ GPA', 'Google', 'https://www.limeconnect.com/programs/page/google-lime-scholarship', 'STEM', True),
            ('Society of Women Engineers Scholarship', 'Multiple scholarships from $1,000 to $15,000 for women in engineering. Over 260 awards given annually. Renewable for multiple years with continued eligibility.', 5000, '2026-02-15', 'Female students pursuing ABET-accredited engineering/technology degree', 'Society of Women Engineers', 'https://scholarships.swe.org/applications/login.asp', 'STEM', True),
            ('SMART Scholarship for Service Program', 'Full ride + stipend + summer internships + guaranteed job after graduation with Department of Defense. Covers full tuition and provides $25,000-$38,000 annual stipend.', 40000, '2025-12-01', 'STEM majors willing to work for DoD after graduation (1 year per year funded)', 'Department of Defense', 'https://www.smartscholarship.org/smart', 'STEM', True),
            ('Lockheed Martin STEM Scholarship', '$10,000 renewable scholarship for students pursuing engineering or computer science. Preference for underrepresented minorities. 200 awards annually.', 10000, '2025-12-31', 'Freshmen or sophomores majoring in engineering/CS with 2.5+ GPA', 'Lockheed Martin', 'https://lockheedmartin.com/en-us/who-we-are/communities/stem-education/scholarships.html', 'STEM', True),
            
            # Business & Economics
            ('Doodle for Google Scholarship', 'Win $30,000 for college plus $50,000 technology package for your school by creating a doodle. Open to K-12 students. Fun and creative way to win scholarship money!', 30000, '2026-03-15', 'K-12 students enrolled in US school - just create an artistic doodle!', 'Google', 'https://doodles.google.com/d4g/', 'Arts', True),
            ('Horatio Alger Scholarship', 'For students who have overcome adversity. Awards range from $7,000 to $25,000. Must demonstrate financial need, perseverance, and involvement in extracurriculars.', 10000, '2025-10-25', 'High school seniors with under $55,000 family income, 2.0+ GPA, faced adversity', 'Horatio Alger Association', 'https://scholars.horatioalger.org/scholarships/', 'Need-Based', True),
            
            # Diversity & Inclusion
            ('Hispanic Scholarship Fund', 'Largest Hispanic scholarship provider in US. Awards from $500 to $5,000. Must be of Hispanic heritage and enrolled in 2-year or 4-year institution.', 5000, '2026-02-15', 'Hispanic heritage students with 3.0+ GPA enrolled in US college', 'Hispanic Scholarship Fund', 'https://www.hsf.net/scholarship', 'Diversity', True),
            ('United Negro College Fund (UNCF)', 'Over 400 different scholarship programs for Black students. Awards range from $500 to $10,000. Must be US citizen or permanent resident.', 5000, '2025-12-31', 'Black/African American students enrolled in UNCF member institution or any accredited college', 'UNCF', 'https://uncf.org/scholarships', 'Diversity', True),
            ('APIASF Scholarship', 'For Asian American and Pacific Islander students. Multiple awards from $2,500 to $20,000. Must demonstrate financial need and be first generation or low income.', 10000, '2026-01-10', 'Asian American/Pacific Islander with financial need, 2.7+ GPA', 'Asian & Pacific Islander American Scholarship Fund', 'https://www.apiasf.org/scholarship_apiasf.html', 'Diversity', True),
            
            # Military & Veterans
            ('Pat Tillman Foundation Scholarship', 'For military veterans and active service members. Awards average $10,000 and includes access to Tillman Scholar Network. Leadership and service focused.', 10000, '2026-02-28', 'Military veterans or active duty service members enrolled in undergraduate or graduate program', 'Pat Tillman Foundation', 'https://pattillmanfoundation.org/apply/', 'Military', True),
            
            # General/Merit
            ('Elks National Foundation Most Valuable Student', 'Competition-based scholarship. 500 awards ranging from $4,000 to $50,000 (renewable for 4 years). Based on academics, leadership, and financial need.', 12500, '2025-11-08', 'High school seniors who are US citizens with financial need', 'Elks National Foundation', 'https://www.elks.org/scholars/scholarships/MVS.cfm', 'National', True),
            ('AXA Achievement Scholarship', '$10,000 scholarships (52 awarded nationally) for students who demonstrate ambition and self-drive. Based on achievement in activities, community service, and academics.', 10000, '2025-12-15', 'High school seniors demonstrating ambition, leadership, determination', 'AXA Foundation', 'https://www.axa.com/en/about-axa/axa-achievement-scholarship', 'National', True),
            ('Foot Locker Scholar Athletes Program', 'For high school athletes who excel academically. 20 awards of $20,000 each. Must be varsity letter winner in NFHS-sanctioned sport.', 20000, '2025-12-17', 'High school seniors with 3.0+ GPA, varsity athlete, community service', 'Foot Locker', 'https://www.footlockerscholarathletes.com/', 'Athletics', True),
            
            # Kansas-Specific REAL Scholarships
            ('Kansas Ethnic Minority Scholarship', 'For Kansas minority students attending Kansas schools. Renewable award up to $1,850 per year. Must be Kansas resident and attend Kansas institution.', 1850, '2026-05-01', 'Kansas residents who are ethnic minority attending Kansas college', 'Kansas Board of Regents', 'https://www.kansasregents.org/students/student_financial_aid/scholarships_and_grants', 'State', True),
            ('Kansas Teacher Service Scholarship', 'For Kansas students pursuing teaching careers. Awards up to $5,514 per year. Requires teaching in Kansas "hard-to-fill" discipline for required service period.', 5514, '2026-05-01', 'Kansas residents pursuing teaching licensure, commit to teach in Kansas', 'Kansas Board of Regents', 'https://www.kansasregents.org/students/student_financial_aid/scholarships_and_grants', 'Education', True),
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
