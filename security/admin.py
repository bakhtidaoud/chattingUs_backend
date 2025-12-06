"""
Admin configuration for security app.
"""

from django.contrib import admin
from .models import TwoFactorAuth, BackupCode


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_enabled', 'is_verified', 'created_at']
    list_filter = ['is_enabled', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['secret_key', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Settings', {
            'fields': ('is_enabled', 'is_verified', 'secret_key')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(BackupCode)
class BackupCodeAdmin(admin.ModelAdmin):
    list_display = ['user', 'code', 'used', 'used_at', 'created_at']
    list_filter = ['used', 'created_at']
    search_fields = ['user__username', 'user__email', 'code']
    readonly_fields = ['code', 'used_at', 'created_at']
    
    def has_add_permission(self, request):
        """Prevent manual creation of backup codes."""
        return False
