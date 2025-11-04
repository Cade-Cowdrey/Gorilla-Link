"""
Scholarship API Integration Module
Connect with multiple scholarship APIs to aggregate real-time data
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
from models import Scholarship
from extensions import db
from loguru import logger
import os

class ScholarshipAPIClient:
    """
    Universal client for connecting to multiple scholarship APIs
    """
    
    def __init__(self):
        # API Keys (store in environment variables)
        self.scholarships_com_key = os.getenv('SCHOLARSHIPS_COM_API_KEY')
        self.fastweb_key = os.getenv('FASTWEB_API_KEY')
        self.going_merry_key = os.getenv('GOING_MERRY_API_KEY')
        self.federal_aid_key = os.getenv('FEDERAL_AID_API_KEY')
    
    # ========================================
    # 1. SCHOLARSHIPS.COM API
    # ========================================
    
    def fetch_from_scholarships_com(self, limit: int = 50) -> List[Dict]:
        """
        Fetch scholarships from Scholarships.com API
        
        API Documentation: https://www.scholarships.com/resources/api/
        Cost: Contact for pricing (often free for edu)
        """
        if not self.scholarships_com_key:
            logger.warning("Scholarships.com API key not configured")
            return []
        
        url = "https://api.scholarships.com/v1/scholarships"
        headers = {
            "Authorization": f"Bearer {self.scholarships_com_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "limit": limit,
            "category": "all",
            "sort": "deadline_asc"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            scholarships = []
            for item in data.get('scholarships', []):
                scholarships.append({
                    'title': item.get('name'),
                    'amount': float(item.get('award_amount', 0)),
                    'provider': item.get('provider', 'Scholarships.com'),
                    'description': item.get('description', ''),
                    'url': item.get('application_url', ''),
                    'deadline': self._parse_date(item.get('deadline')),
                    'category': item.get('category', 'General'),
                    'requirements': item.get('requirements', ''),
                    'source': 'Scholarships.com API'
                })
            
            logger.info(f"Fetched {len(scholarships)} scholarships from Scholarships.com")
            return scholarships
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Scholarships.com: {e}")
            return []
    
    # ========================================
    # 2. FASTWEB API
    # ========================================
    
    def fetch_from_fastweb(self, limit: int = 50) -> List[Dict]:
        """
        Fetch scholarships from Fastweb API
        
        Cost: Free for educational institutions
        Contact: https://www.fastweb.com/contact
        """
        if not self.fastweb_key:
            logger.warning("Fastweb API key not configured")
            return []
        
        url = "https://api.fastweb.com/v1/scholarships"
        headers = {
            "API-Key": self.fastweb_key,
            "Accept": "application/json"
        }
        
        params = {
            "limit": limit,
            "active": True
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            scholarships = []
            for item in data.get('results', []):
                scholarships.append({
                    'title': item.get('title'),
                    'amount': float(item.get('amount', 0)),
                    'provider': item.get('sponsor', 'Fastweb'),
                    'description': item.get('summary', ''),
                    'url': item.get('url', ''),
                    'deadline': self._parse_date(item.get('deadline_date')),
                    'category': item.get('type', 'General'),
                    'requirements': item.get('eligibility', ''),
                    'source': 'Fastweb API'
                })
            
            logger.info(f"Fetched {len(scholarships)} scholarships from Fastweb")
            return scholarships
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Fastweb: {e}")
            return []
    
    # ========================================
    # 3. FEDERAL STUDENT AID API (FREE!)
    # ========================================
    
    def fetch_from_federal_aid(self) -> List[Dict]:
        """
        Fetch federal grants and scholarships
        
        Cost: 100% FREE - No API key required for basic access
        Documentation: https://studentaid.gov/data-center/api
        """
        url = "https://api.studentaid.gov/v1/grants"
        
        # Federal APIs often don't require authentication for public data
        headers = {
            "Accept": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            scholarships = []
            for item in data.get('grants', []):
                scholarships.append({
                    'title': item.get('program_name'),
                    'amount': float(item.get('max_award', 0)),
                    'provider': 'U.S. Department of Education',
                    'description': item.get('description', ''),
                    'url': item.get('info_url', 'https://studentaid.gov'),
                    'deadline': self._parse_date(item.get('deadline')),
                    'category': 'Federal Grant',
                    'requirements': item.get('eligibility', ''),
                    'source': 'Federal Student Aid API'
                })
            
            logger.info(f"Fetched {len(scholarships)} federal grants")
            return scholarships
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Federal Aid API: {e}")
            return []
    
    # ========================================
    # 4. GOING MERRY API
    # ========================================
    
    def fetch_from_going_merry(self, limit: int = 50) -> List[Dict]:
        """
        Fetch scholarships from Going Merry
        
        Cost: Free for students, contact for institutional access
        Website: https://www.goingmerry.com
        """
        if not self.going_merry_key:
            logger.warning("Going Merry API key not configured")
            return []
        
        url = "https://api.goingmerry.com/v1/scholarships"
        headers = {
            "Authorization": f"Token {self.going_merry_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "limit": limit,
            "status": "active"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            scholarships = []
            for item in data.get('scholarships', []):
                scholarships.append({
                    'title': item.get('name'),
                    'amount': float(item.get('award', 0)),
                    'provider': item.get('organization', 'Going Merry'),
                    'description': item.get('description', ''),
                    'url': item.get('application_link', ''),
                    'deadline': self._parse_date(item.get('deadline')),
                    'category': item.get('category', 'General'),
                    'requirements': item.get('criteria', ''),
                    'source': 'Going Merry API'
                })
            
            logger.info(f"Fetched {len(scholarships)} scholarships from Going Merry")
            return scholarships
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Going Merry: {e}")
            return []
    
    # ========================================
    # AGGREGATE ALL SOURCES
    # ========================================
    
    def fetch_all_scholarships(self) -> List[Dict]:
        """
        Aggregate scholarships from all available APIs
        """
        logger.info("Starting scholarship aggregation from all APIs...")
        
        all_scholarships = []
        
        # Fetch from all sources
        all_scholarships.extend(self.fetch_from_scholarships_com(limit=25))
        all_scholarships.extend(self.fetch_from_fastweb(limit=25))
        all_scholarships.extend(self.fetch_from_federal_aid())
        all_scholarships.extend(self.fetch_from_going_merry(limit=25))
        
        # Remove duplicates based on title and provider
        unique_scholarships = self._remove_duplicates(all_scholarships)
        
        logger.info(f"Total unique scholarships fetched: {len(unique_scholarships)}")
        return unique_scholarships
    
    # ========================================
    # SYNC TO DATABASE
    # ========================================
    
    def sync_to_database(self, scholarships: List[Dict]) -> int:
        """
        Sync fetched scholarships to database
        Returns: Number of scholarships added/updated
        """
        count = 0
        
        for scholarship_data in scholarships:
            try:
                # Check if scholarship already exists
                existing = Scholarship.query.filter_by(
                    title=scholarship_data['title'],
                    provider=scholarship_data['provider']
                ).first()
                
                if existing:
                    # Update existing scholarship
                    for key, value in scholarship_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    logger.debug(f"Updated scholarship: {scholarship_data['title']}")
                else:
                    # Create new scholarship
                    new_scholarship = Scholarship(**scholarship_data)
                    db.session.add(new_scholarship)
                    count += 1
                    logger.debug(f"Added scholarship: {scholarship_data['title']}")
                
            except Exception as e:
                logger.error(f"Error syncing scholarship {scholarship_data.get('title')}: {e}")
                continue
        
        try:
            db.session.commit()
            logger.info(f"Successfully synced {count} new scholarships to database")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database commit failed: {e}")
            return 0
        
        return count
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_string:
            return None
        
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return None
    
    def _remove_duplicates(self, scholarships: List[Dict]) -> List[Dict]:
        """Remove duplicate scholarships based on title and provider"""
        seen = set()
        unique = []
        
        for scholarship in scholarships:
            key = (scholarship['title'], scholarship['provider'])
            if key not in seen:
                seen.add(key)
                unique.append(scholarship)
        
        return unique


# ========================================
# AUTOMATED SYNC TASK
# ========================================

def sync_scholarships_from_apis():
    """
    Automated task to sync scholarships from all APIs
    Run this daily via Flask-APScheduler or cron job
    """
    logger.info("🎓 Starting automated scholarship API sync...")
    
    client = ScholarshipAPIClient()
    scholarships = client.fetch_all_scholarships()
    
    if scholarships:
        count = client.sync_to_database(scholarships)
        logger.info(f"✅ Scholarship sync complete: {count} new scholarships added")
    else:
        logger.warning("⚠️ No scholarships fetched from APIs")


# ========================================
# FLASK ROUTE EXAMPLE
# ========================================

"""
# Add this to your blueprints/scholarships/routes.py:

@bp.route("/admin/sync-scholarships", methods=["POST"])
@login_required
@admin_required
def admin_sync_scholarships():
    '''Manual trigger for scholarship API sync'''
    try:
        sync_scholarships_from_apis()
        flash("Scholarship sync started successfully!", "success")
    except Exception as e:
        flash(f"Error syncing scholarships: {str(e)}", "error")
    
    return redirect(url_for("scholarships.admin_dashboard"))
"""


# ========================================
# USAGE EXAMPLE
# ========================================

if __name__ == "__main__":
    # Example: Fetch and sync scholarships
    client = ScholarshipAPIClient()
    
    # Fetch from all APIs
    scholarships = client.fetch_all_scholarships()
    print(f"Fetched {len(scholarships)} scholarships")
    
    # Sync to database
    # count = client.sync_to_database(scholarships)
    # print(f"Synced {count} new scholarships")
