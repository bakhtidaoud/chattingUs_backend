"""
Admin configuration for users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for custom User model.
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('bio', 'profile_picture', 'date_of_birth', 'phone_number', 'is_verified')}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = ['user', 'followers_count', 'following_count', 'posts_count', 'is_private']
    list_filter = ['is_private']
    search_fields = ['user__username', 'user__email']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Admin configuration for Follow model.
    """
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
