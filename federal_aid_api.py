"""
Federal Student Aid API Integration
Free government scholarship and grant data - No API key required!
"""

import requests
from datetime import datetime
from models import Scholarship
from extensions import db
from loguru import logger

class FederalAidAPI:
    """
    Connect to Federal Student Aid API for free government grants and scholarships
    Documentation: https://studentaid.gov/data-center/api
    Cost: 100% FREE - No authentication required
    """
    
    BASE_URL = "https://api.studentaid.gov/v1"
    
    def __init__(self):
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "PittState-Connect/1.0"
        }
    
    def fetch_federal_grants(self):
        """
        Fetch federal grant programs (Pell, FSEOG, TEACH, etc.)
        Returns list of federal scholarships/grants
        """
        logger.info("🇺🇸 Fetching federal grants from Student Aid API...")
        
        scholarships = []
        
        # Manually add known federal programs (API endpoints may vary)
        # These are always available federal grants
        federal_programs = [
            {
                'title': 'Federal Pell Grant',
                'amount': 7395.00,  # 2024-2025 max award
                'provider': 'U.S. Department of Education',
                'description': 'The Federal Pell Grant is awarded to undergraduate students who demonstrate exceptional financial need and have not earned a bachelor\'s, graduate, or professional degree. Award amounts are based on financial need, cost of attendance, and enrollment status.',
                'url': 'https://studentaid.gov/understand-aid/types/grants/pell',
                'deadline': None,  # Rolling deadline
                'category': 'Federal Grant',
                'requirements': 'Must demonstrate financial need, be enrolled in an eligible program, be a U.S. citizen or eligible non-citizen, have a high school diploma or GED, maintain satisfactory academic progress',
                'gpa_requirement': 2.0,
                'is_active': True,
                'source': 'Federal Student Aid'
            },
            {
                'title': 'Federal Supplemental Educational Opportunity Grant (FSEOG)',
                'amount': 4000.00,  # Max per year
                'provider': 'U.S. Department of Education',
                'description': 'The FSEOG program provides grants to undergraduate students with exceptional financial need. Priority is given to students who receive Federal Pell Grants and have the lowest Expected Family Contribution (EFC).',
                'url': 'https://studentaid.gov/understand-aid/types/grants/fseog',
                'deadline': None,  # Administered by schools
                'category': 'Federal Grant',
                'requirements': 'Must have exceptional financial need, be enrolled at least half-time, must be undergraduate student who has not earned a bachelor\'s degree',
                'gpa_requirement': 2.0,
                'is_active': True,
                'source': 'Federal Student Aid'
            },
            {
                'title': 'Teacher Education Assistance for College and Higher Education (TEACH) Grant',
                'amount': 4000.00,  # Per year
                'provider': 'U.S. Department of Education',
                'description': 'The TEACH Grant provides up to $4,000 per year to students who plan to teach in a high-need field at a low-income elementary or secondary school. Recipients must serve as a teacher for at least four years within eight years of completing their program.',
                'url': 'https://studentaid.gov/understand-aid/types/grants/teach',
                'deadline': None,
                'category': 'Education',
                'requirements': 'Must be enrolled in TEACH Grant-eligible program, maintain 3.25 GPA, agree to serve as full-time teacher in high-need field at low-income school for 4 years within 8 years of completing program',
                'gpa_requirement': 3.25,
                'is_active': True,
                'source': 'Federal Student Aid'
            },
            {
                'title': 'Iraq and Afghanistan Service Grant',
                'amount': 7395.00,  # Same as Pell max
                'provider': 'U.S. Department of Education',
                'description': 'This grant is for students whose parent or guardian died as a result of military service in Iraq or Afghanistan after September 11, 2001. Students must be under 24 years old or enrolled in college at least part-time at the time of parent\'s or guardian\'s death.',
                'url': 'https://studentaid.gov/understand-aid/types/grants/iraq-afghanistan-service',
                'deadline': None,
                'category': 'Military/Veterans',
                'requirements': 'Parent or guardian must have died as result of military service in Iraq or Afghanistan after 9/11/2001, student must be under 24 or enrolled at time of death, must not be eligible for Pell Grant based on EFC',
                'gpa_requirement': 2.0,
                'is_active': True,
                'source': 'Federal Student Aid'
            },
            {
                'title': 'Federal Work-Study Program',
                'amount': 5000.00,  # Approximate annual earnings
                'provider': 'U.S. Department of Education',
                'description': 'Federal Work-Study provides part-time jobs for undergraduate and graduate students with financial need, allowing them to earn money to help pay education expenses. Jobs can be on-campus or off-campus with nonprofit or public organizations.',
                'url': 'https://studentaid.gov/understand-aid/types/work-study',
                'deadline': None,
                'category': 'Federal Grant',
                'requirements': 'Must demonstrate financial need, must be enrolled at least half-time, preference given to students with greatest financial need',
                'gpa_requirement': 2.0,
                'is_active': True,
                'source': 'Federal Student Aid'
            }
        ]
        
        scholarships.extend(federal_programs)
        
        # Try to fetch additional data from API if available
        try:
            response = requests.get(
                f"{self.BASE_URL}/grants",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Parse API response if available
                for item in data.get('grants', []):
                    scholarships.append({
                        'title': item.get('program_name'),
                        'amount': float(item.get('max_award', 0)),
                        'provider': 'U.S. Department of Education',
                        'description': item.get('description', ''),
                        'url': item.get('info_url', 'https://studentaid.gov'),
                        'deadline': None,
                        'category': 'Federal Grant',
                        'requirements': item.get('eligibility', ''),
                        'is_active': True,
                        'source': 'Federal Student Aid API'
                    })
                logger.info(f"✅ Fetched {len(data.get('grants', []))} additional grants from API")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"API endpoint not available, using manual data: {e}")
        
        logger.info(f"✅ Total federal grants loaded: {len(scholarships)}")
        return scholarships
    
    def sync_to_database(self):
        """
        Sync federal grants to database
        Returns number of grants added/updated
        """
        logger.info("💾 Syncing federal grants to database...")
        
        scholarships = self.fetch_federal_grants()
        count = 0
        
        for scholarship_data in scholarships:
            try:
                # Check if scholarship exists
                existing = Scholarship.query.filter_by(
                    title=scholarship_data['title'],
                    provider=scholarship_data['provider']
                ).first()
                
                if existing:
                    # Update existing
                    for key, value in scholarship_data.items():
                        if hasattr(existing, key) and value is not None:
                            setattr(existing, key, value)
                    logger.debug(f"Updated: {scholarship_data['title']}")
                else:
                    # Create new
                    new_scholarship = Scholarship(**scholarship_data)
                    db.session.add(new_scholarship)
                    count += 1
                    logger.info(f"✅ Added: {scholarship_data['title']}")
                
            except Exception as e:
                logger.error(f"Error syncing {scholarship_data.get('title')}: {e}")
                continue
        
        try:
            db.session.commit()
            logger.info(f"✅ Successfully synced {count} new federal grants")
            return count
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database commit failed: {e}")
            return 0


# Quick function to add federal grants
def add_federal_grants():
    """
    One-time function to add federal grants to your database
    Run this once to populate federal scholarships
    """
    api = FederalAidAPI()
    count = api.sync_to_database()
    print(f"✅ Added {count} federal grants to database!")
    return count


if __name__ == "__main__":
    # Test the API
    from app import app
    
    with app.app_context():
        print("🇺🇸 Testing Federal Student Aid API...")
        add_federal_grants()
        print("✅ Done!")
