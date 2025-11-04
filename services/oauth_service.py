"""
OAuth Service for PittState Connect
Handles Google, LinkedIn, and Microsoft OAuth 2.0 authentication
"""

from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for, session, redirect, flash
from extensions import db
from models import User
import secrets
import logging

logger = logging.getLogger(__name__)

# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with Flask app"""
    oauth.init_app(app)
    
    # Google OAuth
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'prompt': 'select_account'  # Force account selection
        }
    )
    
    # LinkedIn OAuth
    oauth.register(
        name='linkedin',
        client_id=app.config.get('LINKEDIN_CLIENT_ID'),
        client_secret=app.config.get('LINKEDIN_CLIENT_SECRET'),
        authorize_url='https://www.linkedin.com/oauth/v2/authorization',
        authorize_params=None,
        access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
        access_token_params=None,
        refresh_token_url=None,
        client_kwargs={
            'scope': 'r_liteprofile r_emailaddress',
            'token_endpoint_auth_method': 'client_secret_post'
        }
    )
    
    # Microsoft OAuth
    oauth.register(
        name='microsoft',
        client_id=app.config.get('MICROSOFT_CLIENT_ID'),
        client_secret=app.config.get('MICROSOFT_CLIENT_SECRET'),
        authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        authorize_params=None,
        access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
        access_token_params=None,
        client_kwargs={
            'scope': 'openid email profile User.Read',
            'response_type': 'code'
        }
    )
    
    logger.info("✅ OAuth providers initialized: Google, LinkedIn, Microsoft")


class OAuthService:
    """Service for handling OAuth authentication"""
    
    @staticmethod
    def get_authorization_url(provider):
        """
        Get OAuth authorization URL for provider
        
        Args:
            provider: 'google', 'linkedin', or 'microsoft'
            
        Returns:
            Authorization URL string
        """
        try:
            # Generate state token for CSRF protection
            state = secrets.token_urlsafe(32)
            session['oauth_state'] = state
            session['oauth_provider'] = provider
            
            # Get OAuth client
            client = oauth.create_client(provider)
            if not client:
                logger.error(f"OAuth client not found for provider: {provider}")
                return None
            
            # Generate authorization URL
            redirect_uri = url_for('auth_bp.oauth_callback', provider=provider, _external=True)
            
            if provider == 'google':
                return client.authorize_redirect(redirect_uri, state=state)
            elif provider == 'linkedin':
                return client.authorize_redirect(redirect_uri, state=state)
            elif provider == 'microsoft':
                return client.authorize_redirect(redirect_uri, state=state)
            
        except Exception as e:
            logger.error(f"Error generating OAuth URL for {provider}: {str(e)}")
            return None
    
    @staticmethod
    def handle_callback(provider):
        """
        Handle OAuth callback and create/update user
        
        Args:
            provider: 'google', 'linkedin', or 'microsoft'
            
        Returns:
            tuple: (user, is_new_user, error)
        """
        try:
            # Verify state token
            state = session.get('oauth_state')
            if not state:
                return None, False, "Invalid OAuth state"
            
            # Get OAuth client
            client = oauth.create_client(provider)
            if not client:
                return None, False, f"OAuth client not found: {provider}"
            
            # Get access token
            try:
                token = client.authorize_access_token()
            except Exception as e:
                logger.error(f"Failed to get access token from {provider}: {str(e)}")
                return None, False, f"Failed to authenticate with {provider}"
            
            # Get user info based on provider
            if provider == 'google':
                user_info = OAuthService._get_google_user_info(client, token)
            elif provider == 'linkedin':
                user_info = OAuthService._get_linkedin_user_info(client, token)
            elif provider == 'microsoft':
                user_info = OAuthService._get_microsoft_user_info(client, token)
            else:
                return None, False, f"Unsupported provider: {provider}"
            
            if not user_info:
                return None, False, "Failed to retrieve user information"
            
            # Find or create user
            user, is_new = OAuthService._find_or_create_user(provider, user_info)
            
            # Clear OAuth session data
            session.pop('oauth_state', None)
            session.pop('oauth_provider', None)
            
            return user, is_new, None
            
        except Exception as e:
            logger.error(f"OAuth callback error for {provider}: {str(e)}")
            return None, False, str(e)
    
    @staticmethod
    def _get_google_user_info(client, token):
        """Get user info from Google"""
        try:
            resp = client.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            return {
                'provider_id': data.get('sub'),
                'email': data.get('email'),
                'email_verified': data.get('email_verified', False),
                'first_name': data.get('given_name', ''),
                'last_name': data.get('family_name', ''),
                'full_name': data.get('name', ''),
                'picture': data.get('picture'),
                'locale': data.get('locale')
            }
        except Exception as e:
            logger.error(f"Error getting Google user info: {str(e)}")
            return None
    
    @staticmethod
    def _get_linkedin_user_info(client, token):
        """Get user info from LinkedIn"""
        try:
            # Get profile
            profile_resp = client.get('https://api.linkedin.com/v2/me', token=token)
            if profile_resp.status_code != 200:
                return None
            
            profile = profile_resp.json()
            
            # Get email
            email_resp = client.get(
                'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
                token=token
            )
            email = None
            if email_resp.status_code == 200:
                email_data = email_resp.json()
                elements = email_data.get('elements', [])
                if elements:
                    email = elements[0].get('handle~', {}).get('emailAddress')
            
            first_name = profile.get('localizedFirstName', '')
            last_name = profile.get('localizedLastName', '')
            
            return {
                'provider_id': profile.get('id'),
                'email': email,
                'email_verified': True,  # LinkedIn emails are verified
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}".strip(),
                'picture': None,  # Would need additional API call
                'locale': None
            }
        except Exception as e:
            logger.error(f"Error getting LinkedIn user info: {str(e)}")
            return None
    
    @staticmethod
    def _get_microsoft_user_info(client, token):
        """Get user info from Microsoft"""
        try:
            resp = client.get('https://graph.microsoft.com/v1.0/me', token=token)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            return {
                'provider_id': data.get('id'),
                'email': data.get('mail') or data.get('userPrincipalName'),
                'email_verified': True,  # Microsoft emails are verified
                'first_name': data.get('givenName', ''),
                'last_name': data.get('surname', ''),
                'full_name': data.get('displayName', ''),
                'picture': None,  # Would need additional API call
                'locale': data.get('preferredLanguage')
            }
        except Exception as e:
            logger.error(f"Error getting Microsoft user info: {str(e)}")
            return None
    
    @staticmethod
    def _find_or_create_user(provider, user_info):
        """
        Find existing user or create new one
        
        Returns:
            tuple: (user, is_new_user)
        """
        email = user_info.get('email')
        provider_id = user_info.get('provider_id')
        
        if not email:
            raise ValueError("Email is required for OAuth authentication")
        
        # Check if user exists by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Existing user - update OAuth info
            OAuthService._update_oauth_info(user, provider, provider_id, user_info)
            logger.info(f"Existing user logged in via {provider}: {email}")
            return user, False
        
        # Create new user
        user = OAuthService._create_user_from_oauth(provider, provider_id, user_info)
        logger.info(f"New user created via {provider}: {email}")
        return user, True
    
    @staticmethod
    def _update_oauth_info(user, provider, provider_id, user_info):
        """Update user's OAuth information"""
        try:
            # Store OAuth provider info
            if provider == 'google':
                user.google_id = provider_id
            elif provider == 'linkedin':
                user.linkedin_id = provider_id
            elif provider == 'microsoft':
                user.microsoft_id = provider_id
            
            # Update profile picture if not set
            if not user.profile_image_url and user_info.get('picture'):
                user.profile_image_url = user_info['picture']
            
            # Mark email as verified
            user.email_verified = True
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating OAuth info: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    def _create_user_from_oauth(provider, provider_id, user_info):
        """Create new user from OAuth data"""
        try:
            # Generate username from email
            email = user_info['email']
            username = email.split('@')[0]
            
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user
            user = User(
                username=username,
                email=email,
                email_verified=user_info.get('email_verified', True),
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
                profile_image_url=user_info.get('picture'),
                is_active=True,
                role='student'  # Default role
            )
            
            # Set OAuth provider ID
            if provider == 'google':
                user.google_id = provider_id
            elif provider == 'linkedin':
                user.linkedin_id = provider_id
            elif provider == 'microsoft':
                user.microsoft_id = provider_id
            
            # No password needed for OAuth users
            user.password_hash = None
            
            db.session.add(user)
            db.session.commit()
            
            return user
        except Exception as e:
            logger.error(f"Error creating user from OAuth: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def link_account(user_id, provider, provider_id):
        """
        Link OAuth provider to existing user account
        
        Args:
            user_id: User ID
            provider: OAuth provider name
            provider_id: Provider's user ID
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            if provider == 'google':
                user.google_id = provider_id
            elif provider == 'linkedin':
                user.linkedin_id = provider_id
            elif provider == 'microsoft':
                user.microsoft_id = provider_id
            else:
                return False
            
            db.session.commit()
            logger.info(f"Linked {provider} account for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error linking account: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def unlink_account(user_id, provider):
        """
        Unlink OAuth provider from user account
        
        Args:
            user_id: User ID
            provider: OAuth provider name
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False
            
            # Don't unlink if it's the only auth method
            has_password = user.password_hash is not None
            linked_providers = sum([
                bool(user.google_id),
                bool(user.linkedin_id),
                bool(user.microsoft_id)
            ])
            
            if not has_password and linked_providers <= 1:
                return False  # Would lock user out
            
            if provider == 'google':
                user.google_id = None
            elif provider == 'linkedin':
                user.linkedin_id = None
            elif provider == 'microsoft':
                user.microsoft_id = None
            else:
                return False
            
            db.session.commit()
            logger.info(f"Unlinked {provider} account for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error unlinking account: {str(e)}")
            db.session.rollback()
            return False
