"""
Admin configuration for users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from .models import User, UserProfile, Follow, Block
from core.admin_mixins import ExportMixin


@admin.register(User)
class UserAdmin(ExportMixin, BaseUserAdmin):
    """
    Enhanced admin configuration for custom User model.
    """
    list_display = [
        'profile_picture_thumbnail',
        'username',
        'email',
        'full_name',
        'is_verified',
        'is_active',
        'posts_count_display',
        'followers_count_display',
        'created_at'
    ]
    list_filter = [
        'is_verified',
        'is_staff',
        'is_active',
        'email_verified',
        'phone_verified',
        'created_at',
        'last_login'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    readonly_fields = ['created_at', 'last_login', 'date_joined']
    date_hierarchy = 'created_at'
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('bio', 'profile_picture', 'date_of_birth', 'phone_number')
        }),
        ('Verification', {
            'fields': ('is_verified', 'email_verified', 'phone_verified')
        }),
    )
    
    actions = [
        'ban_users',
        'unban_users',
        'verify_users',
        'unverify_users',
        'export_as_csv',
        'export_as_json'
    ]
    
    def profile_picture_thumbnail(self, obj):
        """Display profile picture thumbnail."""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return format_html('<div style="width: 40px; height: 40px; border-radius: 50%; background: #ddd;"></div>')
    profile_picture_thumbnail.short_description = 'Photo'
    
    def full_name(self, obj):
        """Display full name."""
        return f"{obj.first_name} {obj.last_name}".strip() or '-'
    full_name.short_description = 'Full Name'
    
    def posts_count_display(self, obj):
        """Display posts count."""
        try:
            return obj.posts.count()
        except:
            return 0
    posts_count_display.short_description = 'Posts'
    posts_count_display.admin_order_field = 'posts_count'
    
    def followers_count_display(self, obj):
        """Display followers count."""
        try:
            return obj.followers.count()
        except:
            return 0
    followers_count_display.short_description = 'Followers'
    
    @admin.action(description='Ban selected users')
    def ban_users(self, request, queryset):
        """Ban selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users banned successfully.')
    
    @admin.action(description='Unban selected users')
    def unban_users(self, request, queryset):
        """Unban selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users unbanned successfully.')
    
    @admin.action(description='Verify selected users')
    def verify_users(self, request, queryset):
        """Verify selected users."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users verified successfully.')
    
    @admin.action(description='Unverify selected users')
    def unverify_users(self, request, queryset):
        """Unverify selected users."""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} users unverified successfully.')
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        qs = super().get_queryset(request)
        return qs.annotate(
            posts_count=Count('posts', distinct=True)
        )


@admin.register(UserProfile)
class UserProfileAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.
    """
    list_display = ['user', 'followers_count', 'following_count', 'posts_count', 'is_private']
    list_filter = ['is_private']
    search_fields = ['user__username', 'user__email']
    actions = ['export_as_csv', 'export_as_json']


@admin.register(Follow)
class FollowAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin configuration for Follow model.
    """
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'
    actions = ['export_as_csv', 'export_as_json']


@admin.register(Block)
class BlockAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin configuration for Block model.
    """
    list_display = ['blocker', 'blocked', 'created_at']
    list_filter = ['created_at']
    search_fields = ['blocker__username', 'blocked__username']
    date_hierarchy = 'created_at'
    actions = ['export_as_csv', 'export_as_json']
