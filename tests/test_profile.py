"""
Unit tests for user profile management
Tests profile viewing, editing, and settings
"""

try:
    import pytest
except ImportError:
    pytest = None
    print("pytest not installed. Install with: pip install pytest")

from models import User


class TestProfile:
    """Test cases for profile functionality"""
    
    def test_view_own_profile(self, authenticated_client, sample_user):
        """Test viewing own profile"""
        response = authenticated_client.get(f'/profile/{sample_user.id}')
        assert response.status_code == 200
        assert sample_user.first_name.encode() in response.data
        assert sample_user.last_name.encode() in response.data
    
    def test_view_other_profile(self, authenticated_client, sample_alumni):
        """Test viewing another user's profile"""
        response = authenticated_client.get(f'/profile/{sample_alumni.id}')
        assert response.status_code == 200
        assert sample_alumni.first_name.encode() in response.data
    
    def test_edit_profile_page(self, authenticated_client):
        """Test that edit profile page loads"""
        response = authenticated_client.get('/profile/edit')
        assert response.status_code == 200
        assert b'Edit' in response.data or b'Update' in response.data
    
    def test_update_profile_success(self, authenticated_client, sample_user, db_session):
        """Test successful profile update"""
        new_bio = "Updated bio for testing"
        response = authenticated_client.post('/profile/edit', data={
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': new_bio,
            'location': 'Pittsburg, KS'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify changes in database
        db_session.refresh(sample_user)
        assert sample_user.first_name == 'Updated'
        assert sample_user.last_name == 'Name'
    
    def test_update_profile_validation(self, authenticated_client):
        """Test profile update with invalid data"""
        response = authenticated_client.post('/profile/edit', data={
            'first_name': '',  # Empty first name should fail
            'last_name': 'Name'
        })
        
        assert response.status_code in [200, 400]
    
    def test_change_password(self, authenticated_client, sample_user):
        """Test password change"""
        response = authenticated_client.post('/profile/change-password', data={
            'current_password': 'password123',
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_change_password_wrong_current(self, authenticated_client):
        """Test password change with wrong current password"""
        response = authenticated_client.post('/profile/change-password', data={
            'current_password': 'wrongpassword',
            'new_password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        })
        
        assert response.status_code in [200, 400]
        assert b'incorrect' in response.data.lower() or b'invalid' in response.data.lower()
    
    def test_profile_picture_upload(self, authenticated_client):
        """Test profile picture upload"""
        from io import BytesIO
        
        data = {
            'profile_picture': (BytesIO(b'fake image data'), 'test.jpg')
        }
        
        response = authenticated_client.post(
            '/profile/upload-picture',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Should succeed or fail validation
        assert response.status_code in [200, 400, 302]


@pytest.mark.api
class TestProfileAPI:
    """Test profile API endpoints"""
    
    def test_get_profile_api(self, client, sample_user):
        """Test GET /api/profile endpoint"""
        # Authenticate first
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_user.id)
        
        response = client.get('/api/profile')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['email'] == sample_user.email
        assert data['first_name'] == sample_user.first_name
    
    def test_update_profile_api(self, client, sample_user):
        """Test PUT /api/profile endpoint"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(sample_user.id)
        
        response = client.put('/api/profile', json={
            'first_name': 'Updated',
            'last_name': 'User',
            'bio': 'New bio'
        })
        
        assert response.status_code in [200, 201]
    
    def test_get_user_by_id_api(self, client, sample_alumni):
        """Test GET /api/users/:id endpoint"""
        response = client.get(f'/api/users/{sample_alumni.id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == sample_alumni.id
        assert data['email'] == sample_alumni.email
