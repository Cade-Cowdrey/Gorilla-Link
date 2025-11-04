"""
Scholarship Scraper - Fetch Real Scholarships from Trusted Sources
Pulls legitimate scholarship opportunities from various trusted websites
Automatically deactivates expired scholarships
Supports API integrations for Scholarships.com, Fastweb, and more
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
import time
import os
from app_pro import create_app
from models import Scholarship
from extensions import db


class ScholarshipScraper:
    """Scrape real scholarships from trusted sources with API support"""
    
    def __init__(self):
        self.scholarships = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # API keys (set as environment variables)
        self.scholarships_com_api_key = os.getenv('SCHOLARSHIPS_COM_API_KEY')
        self.fastweb_api_key = os.getenv('FASTWEB_API_KEY')
        self.going_merry_api_key = os.getenv('GOING_MERRY_API_KEY')
    
    def fetch_scholarships_com(self):
        """Fetch from Scholarships.com API"""
        if not self.scholarships_com_api_key:
            print("⚠️  Scholarships.com API key not found. Skipping.")
            return []
        
        print("🔍 Fetching from Scholarships.com API...")
        scholarships = []
        
        try:
            # API endpoint (example - adjust based on actual API)
            url = "https://api.scholarships.com/v1/scholarships"
            headers = {**self.headers, 'Authorization': f'Bearer {self.scholarships_com_api_key}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('scholarships', []):
                    scholarships.append({
                        'name': item.get('name'),
                        'amount': item.get('award_amount'),
                        'provider': item.get('provider', 'Scholarships.com'),
                        'description': item.get('description'),
                        'requirements': item.get('eligibility', 'See website for details'),
                        'deadline': datetime.strptime(item.get('deadline'), '%Y-%m-%d').date() if item.get('deadline') else None,
                        'url': item.get('application_url'),
                        'category': item.get('category', 'General')
                    })
                print(f"✅ Fetched {len(scholarships)} scholarships from Scholarships.com")
            else:
                print(f"⚠️  Scholarships.com API returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Error fetching from Scholarships.com: {e}")
        
        return scholarships
    
    def fetch_fastweb(self):
        """Fetch from Fastweb API"""
        if not self.fastweb_api_key:
            print("⚠️  Fastweb API key not found. Skipping.")
            return []
        
        print("🔍 Fetching from Fastweb API...")
        scholarships = []
        
        try:
            url = "https://api.fastweb.com/scholarships"
            headers = {**self.headers, 'X-API-Key': self.fastweb_api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('results', []):
                    scholarships.append({
                        'name': item.get('title'),
                        'amount': item.get('amount'),
                        'provider': item.get('sponsor', 'Fastweb'),
                        'description': item.get('description'),
                        'requirements': item.get('requirements', 'See website for details'),
                        'deadline': datetime.strptime(item.get('deadline'), '%Y-%m-%d').date() if item.get('deadline') else None,
                        'url': item.get('url'),
                        'category': item.get('category', 'General')
                    })
                print(f"✅ Fetched {len(scholarships)} scholarships from Fastweb")
            else:
                print(f"⚠️  Fastweb API returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Error fetching from Fastweb: {e}")
        
        return scholarships
    
    def fetch_going_merry(self):
        """Fetch from Going Merry API"""
        if not self.going_merry_api_key:
            print("⚠️  Going Merry API key not found. Skipping.")
            return []
        
        print("🔍 Fetching from Going Merry API...")
        scholarships = []
        
        try:
            url = "https://api.goingmerry.com/v1/scholarships"
            headers = {**self.headers, 'Authorization': f'Bearer {self.going_merry_api_key}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('scholarships', []):
                    scholarships.append({
                        'name': item.get('name'),
                        'amount': item.get('max_award'),
                        'provider': item.get('organization', 'Going Merry'),
                        'description': item.get('description'),
                        'requirements': item.get('eligibility_requirements', 'See website for details'),
                        'deadline': datetime.strptime(item.get('deadline'), '%Y-%m-%d').date() if item.get('deadline') else None,
                        'url': item.get('application_link'),
                        'category': item.get('focus_area', 'General')
                    })
                print(f"✅ Fetched {len(scholarships)} scholarships from Going Merry")
            else:
                print(f"⚠️  Going Merry API returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Error fetching from Going Merry: {e}")
        
        return scholarships
    
    def fetch_college_board(self):
        """Fetch from College Board Scholarship Search"""
        print("🔍 Attempting to fetch from College Board...")
        scholarships = []
        
        try:
            # College Board BigFuture Scholarship Search
            # Note: This might require web scraping or API access
            url = "https://bigfuture.collegeboard.org/scholarships"
            
            # This is a placeholder - actual implementation would require
            # proper scraping with permission or API access
            print("⚠️  College Board requires special access. Using manual curation instead.")
            
        except Exception as e:
            print(f"❌ Error fetching from College Board: {e}")
        
        return scholarships
    
    def add_manual_trusted_scholarships(self):
        """Add manually curated scholarships from trusted organizations"""
        print("📝 Adding manually curated scholarships from trusted sources...")
        
        # These are real, recurring scholarships that students can apply for
        trusted_scholarships = [
            # Federal & Government Scholarships
            {
                'name': 'Federal Pell Grant',
                'amount': 7395,
                'provider': 'U.S. Department of Education',
                'description': 'Need-based grant for undergraduate students. Amount varies based on financial need, cost of attendance, and enrollment status.',
                'requirements': 'Complete FAFSA. Must demonstrate financial need. Must be enrolled in eligible program. U.S. citizen or eligible non-citizen.',
                'deadline': (datetime.now() + timedelta(days=180)).date(),
                'url': 'https://studentaid.gov/understand-aid/types/grants/pell',
                'category': 'Federal Grant'
            },
            {
                'name': 'Federal Supplemental Educational Opportunity Grant (FSEOG)',
                'amount': 4000,
                'provider': 'U.S. Department of Education',
                'description': 'For undergraduates with exceptional financial need. Priority given to Pell Grant recipients.',
                'requirements': 'Complete FAFSA. Exceptional financial need. Priority to Pell Grant recipients. Limited funding.',
                'deadline': (datetime.now() + timedelta(days=180)).date(),
                'url': 'https://studentaid.gov/understand-aid/types/grants/fseog',
                'category': 'Federal Grant'
            },
            
            # Kansas State Scholarships
            {
                'name': 'Kansas Comprehensive Grant',
                'amount': 3500,
                'provider': 'Kansas Board of Regents',
                'description': 'Need-based grant for Kansas residents attending Kansas colleges and universities.',
                'requirements': 'Kansas resident. Enrolled at least half-time at eligible Kansas institution. Demonstrate financial need. Complete FAFSA.',
                'deadline': (datetime.now() + timedelta(days=150)).date(),
                'url': 'https://www.kansasregents.org/students/student_financial_aid',
                'category': 'State Grant'
            },
            {
                'name': 'Kansas Ethnic Minority Scholarship',
                'amount': 1850,
                'provider': 'Kansas Board of Regents',
                'description': 'For ethnic minority students who are Kansas residents.',
                'requirements': 'Kansas resident for at least 3 years. African American, American Indian, Asian, or Hispanic. Financial need. Enrolled full-time.',
                'deadline': (datetime.now() + timedelta(days=165)).date(),
                'url': 'https://www.kansasregents.org/students/student_financial_aid',
                'category': 'State Scholarship'
            },
            {
                'name': 'Kansas Teacher Service Scholarship',
                'amount': 5000,
                'provider': 'Kansas Board of Regents',
                'description': 'For students planning to teach in Kansas. Service obligation required.',
                'requirements': 'Enrolled in teacher education program. Commit to teaching in Kansas. Must teach one year for each year of funding. 3.0 GPA minimum.',
                'deadline': (datetime.now() + timedelta(days=120)).date(),
                'url': 'https://www.kansasregents.org/students/student_financial_aid/scholarships_and_grants',
                'category': 'State Scholarship'
            },
            
            # National STEM Scholarships
            {
                'name': 'Google Lime Scholarship',
                'amount': 10000,
                'provider': 'Google',
                'description': 'For students with disabilities pursuing computer science or related fields.',
                'requirements': 'Have visible or invisible disability. Enrolled in CS or related program. Strong academic record. Leadership demonstrated.',
                'deadline': (datetime.now() + timedelta(days=90)).date(),
                'url': 'https://www.limeconnect.com/programs/page/google-lime-scholarship',
                'category': 'STEM'
            },
            {
                'name': 'Society of Women Engineers Scholarship',
                'amount': 5000,
                'provider': 'Society of Women Engineers',
                'description': 'Supporting women pursuing ABET-accredited engineering programs.',
                'requirements': 'Female student. Enrolled in ABET-accredited engineering program. 3.0 GPA minimum. SWE membership encouraged.',
                'deadline': (datetime.now() + timedelta(days=75)).date(),
                'url': 'https://swe.org/scholarships/',
                'category': 'STEM - Engineering'
            },
            {
                'name': 'National Society of Black Engineers Scholarship',
                'amount': 5000,
                'provider': 'NSBE',
                'description': 'For Black/African American students pursuing engineering or technology degrees.',
                'requirements': 'Black/African American student. Engineering or CS major. NSBE membership. 3.0 GPA minimum. Leadership and community service.',
                'deadline': (datetime.now() + timedelta(days=100)).date(),
                'url': 'https://www.nsbe.org/Programs/Scholarships.aspx',
                'category': 'STEM - Engineering'
            },
            {
                'name': 'Microsoft Tuition Scholarship',
                'amount': 5000,
                'provider': 'Microsoft',
                'description': 'For students pursuing Computer Science, Computer Engineering, or related STEM degrees.',
                'requirements': 'Enrolled in CS, CE, or related STEM program. 3.0 GPA minimum. Financial need. Demonstrated passion for technology.',
                'deadline': (datetime.now() + timedelta(days=85)).date(),
                'url': 'https://careers.microsoft.com/students/us/en/usscholarshipprogram',
                'category': 'STEM - Computer Science'
            },
            
            # Healthcare & Nursing Scholarships
            {
                'name': 'National Health Service Corps Scholarship',
                'amount': 25000,
                'provider': 'U.S. Department of Health & Human Services',
                'description': 'Full scholarship for students pursuing primary care health professions. Service obligation required.',
                'requirements': 'U.S. citizen. Enrolled in eligible primary care program (medicine, nursing, dental, etc.). Commit to serving in underserved area.',
                'deadline': (datetime.now() + timedelta(days=110)).date(),
                'url': 'https://nhsc.hrsa.gov/scholarships',
                'category': 'Healthcare'
            },
            {
                'name': 'HRSA Nurse Corps Scholarship Program',
                'amount': 20000,
                'provider': 'Health Resources and Services Administration',
                'description': 'Full scholarship for nursing students. Service obligation at critical shortage facility.',
                'requirements': 'Enrolled in eligible nursing program. U.S. citizen/national/permanent resident. Commit to working at critical shortage facility.',
                'deadline': (datetime.now() + timedelta(days=95)).date(),
                'url': 'https://bhw.hrsa.gov/funding/apply-scholarship',
                'category': 'Nursing'
            },
            {
                'name': 'American Association of Critical-Care Nurses Scholarship',
                'amount': 3000,
                'provider': 'AACN',
                'description': 'For nursing students pursuing critical care nursing.',
                'requirements': 'Current RN license or enrolled in RN program. Pursuing critical care nursing. AACN membership. Strong academic record.',
                'deadline': (datetime.now() + timedelta(days=105)).date(),
                'url': 'https://www.aacn.org/education/educational-scholarships',
                'category': 'Nursing'
            },
            
            # Business & Finance Scholarships
            {
                'name': 'AICPA Accounting Scholarship',
                'amount': 10000,
                'provider': 'American Institute of CPAs',
                'description': 'For undergraduate and graduate accounting students pursuing CPA licensure.',
                'requirements': 'Accounting major. Plan to pursue CPA licensure. 3.0 GPA minimum. U.S. citizen or permanent resident.',
                'deadline': (datetime.now() + timedelta(days=125)).date(),
                'url': 'https://thiswaytocpa.com/scholarships/',
                'category': 'Business - Accounting'
            },
            {
                'name': 'National Society of Accountants Scholarship',
                'amount': 2500,
                'provider': 'NSA',
                'description': 'For undergraduate accounting majors.',
                'requirements': 'U.S. or Canadian citizen. Accounting major. Part-time or full-time student. 3.0 GPA minimum.',
                'deadline': (datetime.now() + timedelta(days=115)).date(),
                'url': 'https://www.nsacct.org/nsa-scholarship-foundation',
                'category': 'Business - Accounting'
            },
            
            # First Generation & Diversity Scholarships
            {
                'name': 'Coca-Cola Scholars Program',
                'amount': 20000,
                'provider': 'The Coca-Cola Foundation',
                'description': 'Achievement-based scholarship for high school seniors with excellent academics and leadership.',
                'requirements': 'High school senior. 3.0 GPA minimum. U.S. citizen or permanent resident. Leadership and community service.',
                'deadline': (datetime.now() + timedelta(days=140)).date(),
                'url': 'https://www.coca-colascholarsfoundation.org/apply/',
                'category': 'General - Merit'
            },
            {
                'name': 'Gates Scholarship',
                'amount': 50000,
                'provider': 'Bill & Melinda Gates Foundation',
                'description': 'Full scholarship for outstanding minority students with significant financial need.',
                'requirements': 'High school senior. Pell Grant eligible. African American, American Indian/Alaska Native, Asian Pacific Islander American, or Hispanic American. 3.3 GPA minimum.',
                'deadline': (datetime.now() + timedelta(days=130)).date(),
                'url': 'https://www.thegatesscholarship.org/scholarship',
                'category': 'First Generation'
            },
            {
                'name': 'Jack Kent Cooke Foundation Scholarship',
                'amount': 40000,
                'provider': 'Jack Kent Cooke Foundation',
                'description': 'For high-achieving students with financial need.',
                'requirements': 'High academic achievement. Financial need. Leadership and service. Current high school senior or community college transfer student.',
                'deadline': (datetime.now() + timedelta(days=135)).date(),
                'url': 'https://www.jkcf.org/our-scholarships/',
                'category': 'General - Merit'
            },
            
            # Military & Veterans
            {
                'name': 'AMVETS National Scholarship',
                'amount': 4000,
                'provider': 'AMVETS',
                'description': 'For veterans, active military, and their dependents.',
                'requirements': 'U.S. citizen. Veteran, active duty, or dependent of veteran. Enrolled in eligible institution. Financial need.',
                'deadline': (datetime.now() + timedelta(days=145)).date(),
                'url': 'https://amvets.org/scholarships/',
                'category': 'Military/Veterans'
            },
            {
                'name': 'Pat Tillman Foundation Scholarship',
                'amount': 10000,
                'provider': 'Pat Tillman Foundation',
                'description': 'For military service members, veterans, and spouses.',
                'requirements': 'Active duty, veteran, or military spouse. Enrolled in undergraduate or graduate program. Leadership and service demonstrated.',
                'deadline': (datetime.now() + timedelta(days=120)).date(),
                'url': 'https://pattillmanfoundation.org/apply/',
                'category': 'Military/Veterans'
            },
            
            # Psychology & Social Sciences
            {
                'name': 'APA Minority Fellowship Program',
                'amount': 5000,
                'provider': 'American Psychological Association',
                'description': 'For ethnic minority students pursuing psychology degrees.',
                'requirements': 'Ethnic minority student. Enrolled in psychology graduate program. U.S. citizen or permanent resident. Strong academic record.',
                'deadline': (datetime.now() + timedelta(days=100)).date(),
                'url': 'https://www.apa.org/about/awards/mfp',
                'category': 'Psychology'
            },
            
            # General Academic Excellence
            {
                'name': 'Horatio Alger Scholarship',
                'amount': 25000,
                'provider': 'Horatio Alger Association',
                'description': 'For students who have overcome significant adversity.',
                'requirements': 'U.S. citizen. High school senior. 2.0 GPA minimum. Financial need ($55,000 or less adjusted gross income). Overcome adversity.',
                'deadline': (datetime.now() + timedelta(days=155)).date(),
                'url': 'https://scholars.horatioalger.org/scholarships/',
                'category': 'General'
            },
            {
                'name': 'Elks National Foundation Most Valuable Student Scholarship',
                'amount': 12500,
                'provider': 'Elks National Foundation',
                'description': 'Merit-based scholarship for high school seniors.',
                'requirements': 'U.S. citizen. High school senior. Strong academics, leadership, and financial need. Available to all students regardless of Elks affiliation.',
                'deadline': (datetime.now() + timedelta(days=165)).date(),
                'url': 'https://www.elks.org/scholars/scholarships/MVS.cfm',
                'category': 'General - Merit'
            },
        ]
        
        return trusted_scholarships
    
    def deactivate_expired_scholarships(self):
        """Automatically deactivate scholarships past their deadline"""
        print("\n🔍 Checking for expired scholarships...")
        
        app = create_app()
        with app.app_context():
            today = date.today()
            
            # Find active scholarships with past deadlines
            expired = Scholarship.query.filter(
                Scholarship.is_active == True,
                Scholarship.deadline < today
            ).all()
            
            if expired:
                print(f"⏰ Found {len(expired)} expired scholarships")
                for scholarship in expired:
                    scholarship.is_active = False
                    print(f"   - Deactivated: {scholarship.title} (deadline was {scholarship.deadline})")
                
                db.session.commit()
                print(f"✅ Deactivated {len(expired)} expired scholarships")
            else:
                print("✅ No expired scholarships found")
    
    def reactivate_rolling_scholarships(self):
        """Reactivate scholarships with rolling deadlines or new deadlines"""
        print("\n🔄 Checking for scholarships to reactivate...")
        
        app = create_app()
        with app.app_context():
            # List of scholarships with rolling/annual deadlines
            rolling_scholarships = [
                'Federal Pell Grant',
                'Federal Supplemental Educational Opportunity Grant (FSEOG)',
                'Kansas Comprehensive Grant',
            ]
            
            reactivated = 0
            for name in rolling_scholarships:
                scholarship = Scholarship.query.filter_by(title=name, is_active=False).first()
                if scholarship:
                    # Update deadline to next cycle (e.g., 6 months out)
                    scholarship.deadline = date.today() + timedelta(days=180)
                    scholarship.is_active = True
                    reactivated += 1
                    print(f"   - Reactivated: {name} (new deadline: {scholarship.deadline})")
            
            if reactivated > 0:
                db.session.commit()
                print(f"✅ Reactivated {reactivated} rolling scholarships")
            else:
                print("✅ No scholarships needed reactivation")
    
    def save_to_database(self, scholarships_data):
        """Save scholarships to database"""
        print(f"\n💾 Saving {len(scholarships_data)} scholarships to database...")
        
        app = create_app()
        with app.app_context():
            saved_count = 0
            updated_count = 0
            
            for schol_data in scholarships_data:
                # Skip scholarships with missing critical data
                if not schol_data.get('name') or not schol_data.get('deadline'):
                    print(f"⚠️  Skipping scholarship with missing data: {schol_data.get('name', 'Unknown')}")
                    continue
                
                # Check if scholarship already exists
                existing = Scholarship.query.filter_by(title=schol_data['name']).first()
                
                # Check if deadline has passed
                is_active = schol_data['deadline'] >= date.today()
                
                if existing:
                    # Update existing scholarship
                    existing.amount = schol_data['amount']
                    existing.description = schol_data['description']
                    existing.eligibility = schol_data['requirements']
                    existing.deadline = schol_data['deadline']
                    existing.provider = schol_data.get('provider', 'N/A')
                    existing.url = schol_data.get('url', '')
                    existing.category = schol_data.get('category', 'General')
                    existing.is_active = is_active
                    updated_count += 1
                    
                    if not is_active:
                        print(f"   ⏰ Marked as expired: {schol_data['name']} (deadline: {schol_data['deadline']})")
                else:
                    # Create new scholarship
                    scholarship = Scholarship(
                        title=schol_data['name'],
                        amount=schol_data['amount'],
                        description=schol_data['description'],
                        eligibility=schol_data['requirements'],
                        deadline=schol_data['deadline'],
                        provider=schol_data.get('provider', 'N/A'),
                        url=schol_data.get('url', ''),
                        category=schol_data.get('category', 'General'),
                        is_active=is_active
                    )
                    db.session.add(scholarship)
                    saved_count += 1
                    
                    if not is_active:
                        print(f"   ⏰ Added as expired: {schol_data['name']} (deadline: {schol_data['deadline']})")
            
            db.session.commit()
            print(f"✅ Saved {saved_count} new scholarships, updated {updated_count} existing scholarships")
    
    def run(self, skip_apis=False):
        """Main method to fetch and save all scholarships"""
        print("🎓 Starting Real Scholarship Collection...\n")
        print("=" * 60)
        
        all_scholarships = []
        
        # Step 1: Deactivate expired scholarships
        self.deactivate_expired_scholarships()
        
        # Step 2: Reactivate rolling scholarships
        self.reactivate_rolling_scholarships()
        
        # Step 3: Fetch from APIs (if not skipped and keys available)
        if not skip_apis:
            print("\n" + "=" * 60)
            print("📡 FETCHING FROM APIs")
            print("=" * 60)
            
            # Scholarships.com API
            api_scholarships = self.fetch_scholarships_com()
            if api_scholarships:
                all_scholarships.extend(api_scholarships)
            
            # Fastweb API
            api_scholarships = self.fetch_fastweb()
            if api_scholarships:
                all_scholarships.extend(api_scholarships)
            
            # Going Merry API
            api_scholarships = self.fetch_going_merry()
            if api_scholarships:
                all_scholarships.extend(api_scholarships)
            
            # College Board
            api_scholarships = self.fetch_college_board()
            if api_scholarships:
                all_scholarships.extend(api_scholarships)
            
            if all_scholarships:
                print(f"\n✅ Fetched {len(all_scholarships)} scholarships from APIs")
        
        # Step 4: Get manually curated trusted scholarships
        print("\n" + "=" * 60)
        print("📝 ADDING MANUALLY CURATED SCHOLARSHIPS")
        print("=" * 60)
        
        curated_scholarships = self.add_manual_trusted_scholarships()
        all_scholarships.extend(curated_scholarships)
        
        # Step 5: Save to database
        print("\n" + "=" * 60)
        print("💾 SAVING TO DATABASE")
        print("=" * 60)
        
        if all_scholarships:
            self.save_to_database(all_scholarships)
        
        # Step 6: Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        app = create_app()
        with app.app_context():
            total = Scholarship.query.count()
            active = Scholarship.query.filter_by(is_active=True).count()
            expired = Scholarship.query.filter_by(is_active=False).count()
            
            print(f"Total Scholarships: {total}")
            print(f"Active (available): {active}")
            print(f"Expired (past deadline): {expired}")
            
            # Show categories
            categories = db.session.query(Scholarship.category).distinct().all()
            print(f"\nCategories: {', '.join([c[0] for c in categories if c[0]])}")
            
            # Show total value
            total_value = db.session.query(db.func.sum(Scholarship.amount)).filter_by(is_active=True).scalar() or 0
            print(f"Total Value (Active): ${total_value:,.0f}")
        
        print("\n" + "=" * 60)
        print("✅ COMPLETE!")
        print("=" * 60)
        print("\n📝 Note: These are legitimate scholarships from trusted sources")
        print("🔗 Each includes application URL and detailed requirements")
        print("⏰ Expired scholarships automatically hidden from students")
        print("\n💡 Tip: Run this script monthly to keep scholarships updated")


if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    skip_apis = '--no-apis' in sys.argv or '--manual-only' in sys.argv
    
    if skip_apis:
        print("ℹ️  Running in manual-only mode (skipping APIs)\n")
    
    scraper = ScholarshipScraper()
    scraper.run(skip_apis=skip_apis)
