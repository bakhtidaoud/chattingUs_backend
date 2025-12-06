"""
Authentication and JWT token tests.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestAuthentication:
    """Test authentication functionality."""
    
    def test_jwt_token_generation(self, user):
        """Test JWT token generation."""
        refresh = RefreshToken.for_user(user)
        assert str(refresh.access_token)
        assert str(refresh)
        assert refresh['user_id'] == user.id
    
    def test_access_token_validation(self, user):
        """Test access token validation."""
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Validate token
        token = AccessToken(access_token)
        assert token['user_id'] == user.id
    
    def test_refresh_token_validation(self, user):
        """Test refresh token validation."""
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        
        # Validate token
        token = RefreshToken(refresh_token)
        assert token['user_id'] == user.id
    
    def test_invalid_token(self):
        """Test invalid token raises error."""
        with pytest.raises(TokenError):
            AccessToken('invalid_token')
    
    def test_token_refresh_endpoint(self, api_client, user):
        """Test token refresh endpoint."""
        refresh = RefreshToken.for_user(user)
        url = reverse('token_refresh')
        response = api_client.post(url, {'refresh': str(refresh)})
        
        assert response.status_code == 200
        assert 'access' in response.data
        # New access token should be different
        assert response.data['access'] != str(refresh.access_token)
    
    def test_token_blacklist_on_logout(self, authenticated_client, user_tokens):
        """Test token blacklisting on logout."""
        url = reverse('token_blacklist')
        response = authenticated_client.post(url, {'refresh': user_tokens['refresh']})
        
        assert response.status_code == 200
        
        # Try to use blacklisted token
        refresh_url = reverse('token_refresh')
        response = authenticated_client.post(refresh_url, {'refresh': user_tokens['refresh']})
        assert response.status_code == 401
    
    def test_password_reset_request(self, api_client, user):
        """Test password reset request."""
        url = reverse('password-reset')
        data = {'email': user.email}
        response = api_client.post(url, data)
        
        assert response.status_code == 200
        # Email would be sent in real scenario
    
    def test_password_change(self, authenticated_client, user):
        """Test password change."""
        url = reverse('password-change')
        data = {
            'old_password': 'testpass123!',
            'new_password': 'newpass456!',
            'new_password2': 'newpass456!'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 200
        
        # Verify new password works
        user.refresh_from_db()
        assert user.check_password('newpass456!')
    
    def test_password_change_wrong_old_password(self, authenticated_client):
        """Test password change with wrong old password."""
        url = reverse('password-change')
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456!',
            'new_password2': 'newpass456!'
        }
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestPermissions:
    """Test permission and access control."""
    
    def test_authenticated_user_can_access_protected_endpoint(self, authenticated_client):
        """Test authenticated users can access protected endpoints."""
        url = reverse('user-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
    
    def test_unauthenticated_user_cannot_access_protected_endpoint(self, api_client):
        """Test unauthenticated users cannot access protected endpoints."""
        url = reverse('user-list')
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_user_can_edit_own_content(self, authenticated_client, user):
        """Test users can edit their own content."""
        url = reverse('user-detail', kwargs={'pk': user.pk})
        data = {'bio': 'New bio'}
        response = authenticated_client.patch(url, data)
        assert response.status_code == 200
    
    def test_user_cannot_edit_others_content(self, authenticated_client, user2):
        """Test users cannot edit others' content."""
        url = reverse('user-detail', kwargs={'pk': user2.pk})
        data = {'bio': 'Hacked bio'}
        response = authenticated_client.patch(url, data)
        assert response.status_code == 403
    
    def test_admin_can_access_admin_endpoints(self, admin_client):
        """Test admin users can access admin endpoints."""
        # Admin-specific test would go here
        pass
    
    def test_regular_user_cannot_access_admin_endpoints(self, authenticated_client):
        """Test regular users cannot access admin endpoints."""
        # Admin-specific test would go here
        pass
