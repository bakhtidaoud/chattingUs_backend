"""
Admin configuration for system_settings app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import FeatureFlag, SystemSetting, MaintenanceMode
from core.admin_mixins import ExportMixin


@admin.register(FeatureFlag)
class FeatureFlagAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin configuration for FeatureFlag model.
    """
    list_display = ['status_icon', 'name', 'description_short', 'is_enabled', 'updated_at']
    list_filter = ['is_enabled', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Feature Information', {
            'fields': ('name', 'description', 'is_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = [
        'enable_features',
        'disable_features',
        'export_as_csv',
        'export_as_json'
    ]
    
    def status_icon(self, obj):
        """Display status icon."""
        if obj.is_enabled:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    status_icon.short_description = ''
    
    def description_short(self, obj):
        """Display shortened description."""
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Description'
    
    @admin.action(description='Enable selected features')
    def enable_features(self, request, queryset):
        """Enable selected features."""
        updated = queryset.update(is_enabled=True)
        self.message_user(request, f'{updated} features enabled.')
    
    @admin.action(description='Disable selected features')
    def disable_features(self, request, queryset):
        """Disable selected features."""
        updated = queryset.update(is_enabled=False)
        self.message_user(request, f'{updated} features disabled.')


@admin.register(SystemSetting)
class SystemSettingAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin configuration for SystemSetting model.
    """
    list_display = ['key', 'value_display', 'setting_type', 'is_public', 'updated_at']
    list_filter = ['setting_type', 'is_public', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Setting Information', {
            'fields': ('key', 'value', 'description', 'setting_type')
        }),
        ('Access', {
            'fields': ('is_public',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['export_as_csv', 'export_as_json']
    
    def value_display(self, obj):
        """Display value (truncated if long)."""
        value = obj.value
        if len(value) > 50:
            return value[:50] + '...'
        return value
    value_display.short_description = 'Value'


@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    """
    Admin configuration for MaintenanceMode model.
    """
    list_display = ['status_display', 'message_short', 'start_time', 'end_time', 'bypass_for_staff']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Status', {
            'fields': ('is_enabled',),
            'description': 'Enable or disable maintenance mode'
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time'),
            'description': 'Optional: Schedule maintenance window'
        }),
        ('Access Control', {
            'fields': ('allowed_ips', 'bypass_for_staff')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def status_display(self, obj):
        """Display maintenance status."""
        if obj.is_enabled:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">ACTIVE</span>'
            )
        return format_html(
            '<span style="background: #28a745; color: white; padding: 5px 10px; border-radius: 3px;">Inactive</span>'
        )
    status_display.short_description = 'Status'
    
    def message_short(self, obj):
        """Display shortened message."""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'
    
    def has_add_permission(self, request):
        """Only allow one maintenance mode instance."""
        return not MaintenanceMode.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of maintenance mode."""
        return False
