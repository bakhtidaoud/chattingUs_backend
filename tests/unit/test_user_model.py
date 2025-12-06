"""
Unit tests for User model.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.unit
class TestUserModel:
    """Test User model."""
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123!'
        )
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.check_password('newpass123!')
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123!'
        )
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.is_active
    
    def test_user_str(self, user):
        """Test user string representation."""
        assert str(user) == 'testuser'
    
    def test_user_email_unique(self, user):
        """Test that email must be unique."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='another',
                email='test@example.com',  # Same email
                password='pass123!'
            )
    
    def test_user_username_unique(self, user):
        """Test that username must be unique."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='testuser',  # Same username
                email='another@example.com',
                password='pass123!'
            )
    
    def test_user_verification(self, user):
        """Test user verification."""
        assert not user.is_verified
        user.is_verified = True
        user.save()
        user.refresh_from_db()
        assert user.is_verified
    
    def test_user_email_verification(self, user):
        """Test email verification."""
        assert not user.email_verified
        user.email_verified = True
        user.save()
        user.refresh_from_db()
        assert user.email_verified
    
    def test_user_phone_verification(self, user):
        """Test phone verification."""
        assert not user.phone_verified
        user.phone_number = '+1234567890'
        user.phone_verified = True
        user.save()
        user.refresh_from_db()
        assert user.phone_verified
        assert user.phone_number == '+1234567890'
    
    def test_user_profile_picture(self, user):
        """Test user profile picture."""
        assert not user.profile_picture
        # Profile picture would be tested with actual file upload
    
    def test_user_bio(self, user):
        """Test user bio."""
        user.bio = 'This is my bio'
        user.save()
        user.refresh_from_db()
        assert user.bio == 'This is my bio'
    
    def test_user_date_of_birth(self, user):
        """Test user date of birth."""
        from datetime import date
        dob = date(1990, 1, 1)
        user.date_of_birth = dob
        user.save()
        user.refresh_from_db()
        assert user.date_of_birth == dob
