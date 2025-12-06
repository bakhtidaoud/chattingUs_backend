"""
Integration tests for User API endpoints.
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.integration
class TestUserAPI:
    """Test User API endpoints."""
    
    def test_user_registration(self, api_client):
        """Test user registration endpoint."""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123!',
            'password2': 'newpass123!'
        }
        response = api_client.post(url, data)
        assert response.status_code == 201
        assert 'user' in response.data
        assert User.objects.filter(username='newuser').exists()
    
    def test_user_registration_invalid_password(self, api_client):
        """Test registration with invalid password."""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': '123',  # Too short
            'password2': '123'
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
    
    def test_user_registration_password_mismatch(self, api_client):
        """Test registration with password mismatch."""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123!',
            'password2': 'different123!'
        }
        response = api_client.post(url, data)
        assert response.status_code == 400
    
    def test_user_login(self, api_client, user):
        """Test user login endpoint."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123!'
        }
        response = api_client.post(url, data)
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_user_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = api_client.post(url, data)
        assert response.status_code == 401
    
    def test_token_refresh(self, api_client, user_tokens):
        """Test token refresh endpoint."""
        url = reverse('token_refresh')
        data = {'refresh': user_tokens['refresh']}
        response = api_client.post(url, data)
        assert response.status_code == 200
        assert 'access' in response.data
    
    def test_get_user_profile(self, authenticated_client, user):
        """Test getting user profile."""
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'
    
    def test_update_user_profile(self, authenticated_client, user):
        """Test updating user profile."""
        url = reverse('user-detail', kwargs={'pk': user.pk})
        data = {
            'bio': 'Updated bio',
            'first_name': 'Updated'
        }
        response = authenticated_client.patch(url, data)
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.bio == 'Updated bio'
        assert user.first_name == 'Updated'
    
    def test_cannot_update_other_user_profile(self, authenticated_client, user2):
        """Test that users cannot update other users' profiles."""
        url = reverse('user-detail', kwargs={'pk': user2.pk})
        data = {'bio': 'Hacked bio'}
        response = authenticated_client.patch(url, data)
        assert response.status_code == 403
    
    def test_list_users(self, authenticated_client, user, user2):
        """Test listing users."""
        url = reverse('user-list')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert len(response.data['results']) >= 2
    
    def test_search_users(self, authenticated_client, user, user2):
        """Test searching users."""
        url = reverse('user-list')
        response = authenticated_client.get(url, {'search': 'testuser2'})
        assert response.status_code == 200
        assert len(response.data['results']) >= 1
        assert response.data['results'][0]['username'] == 'testuser2'
    
    def test_unauthorized_access(self, api_client):
        """Test that unauthorized users cannot access protected endpoints."""
        url = reverse('user-list')
        response = api_client.get(url)
        assert response.status_code == 401
