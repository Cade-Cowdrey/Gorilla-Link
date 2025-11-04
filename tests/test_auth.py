"""
Unit tests for authentication endpoints
Tests login, logout, registration, password reset
"""

import pytest
from flask import url_for
from models import User


class TestAuthentication:
    """Test cases for authentication functionality"""
    
    def test_registration_page_loads(self, client):
        """Test that registration page loads successfully"""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Register' in response.data or b'Sign Up' in response.data
    
    def test_successful_registration(self, client, db_session):
        """Test successful user registration"""
        response = client.post('/auth/register', data={
            'email': 'newuser@pittstate.edu',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'student',
            'graduation_year': 2025,
            'major': 'Computer Science'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        user = User.query.filter_by(email='newuser@pittstate.edu').first()
        assert user is not None
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert user.role == 'student'
    
    def test_registration_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email"""
        response = client.post('/auth/register', data={
            'email': sample_user.email,
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'Duplicate',
            'last_name': 'User'
        })
        
        assert response.status_code in [200, 400]
        assert b'already exists' in response.data or b'already registered' in response.data
    
    def test_registration_password_mismatch(self, client):
        """Test registration with mismatched passwords"""
        response = client.post('/auth/register', data={
            'email': 'test@pittstate.edu',
            'password': 'SecurePass123!',
            'confirm_password': 'DifferentPass456!',
            'first_name': 'Test',
            'last_name': 'User'
        })
        
        assert response.status_code in [200, 400]
        assert b'match' in response.data.lower()
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'Sign In' in response.data
    
    def test_successful_login(self, client, sample_user):
        """Test successful login"""
        response = client.post('/auth/login', data={
            'email': sample_user.email,
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check if redirected to dashboard or home
        assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@pittstate.edu',
            'password': 'password123'
        })
        
        assert response.status_code in [200, 401]
        assert b'Invalid' in response.data or b'incorrect' in response.data.lower()
    
    def test_login_invalid_password(self, client, sample_user):
        """Test login with invalid password"""
        response = client.post('/auth/login', data={
            'email': sample_user.email,
            'password': 'wrongpassword'
        })
        
        assert response.status_code in [200, 401]
        assert b'Invalid' in response.data or b'incorrect' in response.data.lower()
    
    def test_logout(self, authenticated_client):
        """Test logout functionality"""
        response = authenticated_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Try to access protected page after logout
        response = authenticated_client.get('/profile')
        assert response.status_code in [302, 401]  # Should redirect to login
    
    def test_password_reset_request(self, client, sample_user):
        """Test password reset request"""
        response = client.post('/auth/forgot-password', data={
            'email': sample_user.email
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestAuthorizationDecorators:
    """Test authorization and role-based access control"""
    
    def test_login_required_decorator(self, client):
        """Test that @login_required blocks unauthenticated users"""
        response = client.get('/profile')
        assert response.status_code in [302, 401]  # Redirect to login or 401
    
    def test_admin_required_decorator(self, authenticated_client):
        """Test that @admin_required blocks non-admin users"""
        response = authenticated_client.get('/admin/dashboard')
        assert response.status_code in [302, 403]  # Redirect or forbidden
    
    def test_admin_access_granted(self, admin_client):
        """Test that admin users can access admin pages"""
        response = admin_client.get('/admin/dashboard')
        assert response.status_code == 200


@pytest.mark.api
class TestAuthenticationAPI:
    """Test authentication API endpoints"""
    
    def test_api_login_success(self, client, sample_user):
        """Test API login endpoint"""
        response = client.post('/api/auth/login', json={
            'email': sample_user.email,
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data or 'success' in data
    
    def test_api_login_invalid_credentials(self, client):
        """Test API login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'email': 'invalid@pittstate.edu',
            'password': 'wrongpass'
        })
        
        assert response.status_code in [400, 401]
        data = response.get_json()
        assert 'error' in data
    
    def test_api_token_validation(self, client, sample_user):
        """Test API token validation"""
        # First, get a token
        login_response = client.post('/api/auth/login', json={
            'email': sample_user.email,
            'password': 'password123'
        })
        
        if login_response.status_code == 200:
            data = login_response.get_json()
            token = data.get('token')
            
            if token:
                # Use token to access protected endpoint
                response = client.get('/api/profile', headers={
                    'Authorization': f'Bearer {token}'
                })
                
                assert response.status_code == 200
