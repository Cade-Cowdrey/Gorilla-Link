"""
LinkedIn Integration for Graduate Outcome Tracking
OAuth2 integration with LinkedIn API to automatically track graduate employment data
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from loguru import logger
import os

class LinkedInIntegrator:
    """Handles LinkedIn OAuth and data synchronization"""
    
    def __init__(self):
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'https://pittstate-connect.onrender.com/auth/linkedin/callback')
        
        self.auth_url = 'https://www.linkedin.com/oauth/v2/authorization'
        self.token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        self.api_base = 'https://api.linkedin.com/v2'
        
        # Required scopes for profile and employment data
        self.scopes = [
            'r_liteprofile',  # Basic profile info
            'r_emailaddress',  # Email
            'r_fullprofile',   # Full profile including employment
        ]
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate LinkedIn OAuth authorization URL
        
        Args:
            state: Random string to prevent CSRF attacks
            
        Returns:
            Authorization URL for user to visit
        """
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
        }
        
        if state:
            params['state'] = state
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from LinkedIn callback
            
        Returns:
            Token data including access_token, expires_in
        """
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Calculate expiration datetime
            expires_in = token_data.get('expires_in', 5184000)  # Default 60 days
            token_data['expires_at'] = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return token_data
        except Exception as e:
            logger.error(f"LinkedIn token exchange error: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh an expired access token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token data
        """
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            expires_in = token_data.get('expires_in', 5184000)
            token_data['expires_at'] = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return token_data
        except Exception as e:
            logger.error(f"LinkedIn token refresh error: {e}")
            return None
    
    def get_profile_data(self, access_token: str) -> Optional[Dict]:
        """
        Fetch user's LinkedIn profile data
        
        Args:
            access_token: Valid OAuth access token
            
        Returns:
            Profile data dictionary
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Get basic profile
            profile_url = f"{self.api_base}/me"
            profile_response = requests.get(profile_url, headers=headers)
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            
            # Get email
            email_url = f"{self.api_base}/emailAddress?q=members&projection=(elements*(handle~))"
            email_response = requests.get(email_url, headers=headers)
            email_response.raise_for_status()
            email_data = email_response.json()
            
            # Get full profile with employment
            full_profile_url = f"{self.api_base}/me?projection=(id,firstName,lastName,headline,profilePicture,positions)"
            full_response = requests.get(full_profile_url, headers=headers)
            full_response.raise_for_status()
            full_data = full_response.json()
            
            return {
                'profile': profile_data,
                'email': email_data,
                'full_profile': full_data
            }
        except Exception as e:
            logger.error(f"LinkedIn profile fetch error: {e}")
            return None
    
    def get_employment_history(self, access_token: str) -> List[Dict]:
        """
        Fetch user's employment history from LinkedIn
        
        Args:
            access_token: Valid OAuth access token
            
        Returns:
            List of employment positions
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Get positions
            url = f"{self.api_base}/me?projection=(positions)"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            positions = data.get('positions', {}).get('values', [])
            
            employment_history = []
            for position in positions:
                employment_history.append({
                    'title': position.get('title'),
                    'company': position.get('company', {}).get('name'),
                    'company_id': position.get('company', {}).get('id'),
                    'location': position.get('location', {}).get('name'),
                    'description': position.get('summary'),
                    'start_date': self._parse_linkedin_date(position.get('startDate')),
                    'end_date': self._parse_linkedin_date(position.get('endDate')),
                    'is_current': position.get('isCurrent', False)
                })
            
            return employment_history
        except Exception as e:
            logger.error(f"LinkedIn employment history error: {e}")
            return []
    
    def get_current_position(self, access_token: str) -> Optional[Dict]:
        """
        Get user's current employment position
        
        Args:
            access_token: Valid OAuth access token
            
        Returns:
            Current position data or None
        """
        employment_history = self.get_employment_history(access_token)
        
        for position in employment_history:
            if position.get('is_current'):
                return position
        
        # If no current position marked, return most recent
        if employment_history:
            return employment_history[0]
        
        return None
    
    def _parse_linkedin_date(self, date_obj: Dict) -> Optional[str]:
        """
        Parse LinkedIn date format to ISO string
        
        Args:
            date_obj: LinkedIn date object with year, month
            
        Returns:
            ISO format date string
        """
        if not date_obj:
            return None
        
        try:
            year = date_obj.get('year')
            month = date_obj.get('month', 1)
            day = date_obj.get('day', 1)
            
            if year:
                return f"{year}-{month:02d}-{day:02d}"
        except Exception:
            pass
        
        return None
    
    def sync_profile_to_database(self, user_id: int, access_token: str):
        """
        Sync LinkedIn data to database
        
        Args:
            user_id: User ID in database
            access_token: Valid OAuth access token
        """
        from models import db
        from models_growth_features import LinkedInProfile
        
        try:
            # Fetch profile data
            profile_data = self.get_profile_data(access_token)
            if not profile_data:
                return False
            
            employment_history = self.get_employment_history(access_token)
            current_position = self.get_current_position(access_token)
            
            # Get or create LinkedIn profile
            linkedin_profile = LinkedInProfile.query.filter_by(user_id=user_id).first()
            if not linkedin_profile:
                linkedin_profile = LinkedInProfile(user_id=user_id)
                db.session.add(linkedin_profile)
            
            # Update profile data
            full_profile = profile_data.get('full_profile', {})
            linkedin_profile.linkedin_id = full_profile.get('id')
            linkedin_profile.headline = full_profile.get('headline')
            
            # Update current position
            if current_position:
                linkedin_profile.current_position = current_position.get('title')
                linkedin_profile.current_company = current_position.get('company')
                linkedin_profile.location = current_position.get('location')
            
            # Update employment history
            linkedin_profile.employment_history = employment_history
            
            # Calculate total experience
            linkedin_profile.total_experience_years = self._calculate_experience_years(employment_history)
            
            # Update sync timestamp
            linkedin_profile.last_synced = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Synced LinkedIn profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"LinkedIn sync error: {e}")
            db.session.rollback()
            return False
    
    def _calculate_experience_years(self, employment_history: List[Dict]) -> int:
        """Calculate total years of experience from employment history"""
        if not employment_history:
            return 0
        
        total_days = 0
        for position in employment_history:
            start_date = position.get('start_date')
            end_date = position.get('end_date') or datetime.utcnow().strftime('%Y-%m-%d')
            
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else datetime.utcnow()
                    
                    days = (end - start).days
                    total_days += max(0, days)
                except Exception:
                    pass
        
        return total_days // 365
    
    def create_outcome_report_from_linkedin(self, user_id: int) -> bool:
        """
        Automatically create OutcomeReport from LinkedIn data
        
        Args:
            user_id: User ID
            
        Returns:
            Success boolean
        """
        from models import db, User
        from models_growth_features import LinkedInProfile, OutcomeReport
        
        try:
            linkedin_profile = LinkedInProfile.query.filter_by(user_id=user_id).first()
            if not linkedin_profile:
                return False
            
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Check if outcome report already exists
            existing_report = OutcomeReport.query.filter_by(user_id=user_id).first()
            
            current_position = linkedin_profile.get_current_role()
            if not current_position:
                return False
            
            if not existing_report:
                outcome_report = OutcomeReport(user_id=user_id)
                db.session.add(outcome_report)
            else:
                outcome_report = existing_report
            
            # Update outcome data from LinkedIn
            outcome_report.outcome_type = 'employed'
            outcome_report.employer_name = current_position.get('company')
            outcome_report.job_title = current_position.get('title')
            outcome_report.location = current_position.get('location')
            outcome_report.employment_status = 'full_time'  # Assume full-time
            
            # Mark as synced from LinkedIn
            outcome_report.data_source = 'linkedin'
            outcome_report.last_updated = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Created outcome report from LinkedIn for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Outcome report creation error: {e}")
            db.session.rollback()
            return False


# Singleton instance
linkedin_integrator = LinkedInIntegrator()
