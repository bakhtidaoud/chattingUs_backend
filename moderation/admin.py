"""
Admin configuration for moderation app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Report, ModerationAction
from core.admin_mixins import ExportMixin


@admin.register(Report)
class ReportAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin configuration for Report model.
    """
    list_display = [
        'id',
        'reporter',
        'report_type_badge',
        'status_badge',
        'content_preview',
        'created_at'
    ]
    list_filter = ['status', 'report_type', 'created_at']
    search_fields = ['reporter__username', 'description']
    readonly_fields = ['reporter', 'content_type', 'object_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'report_type', 'description', 'status')
        }),
        ('Reported Content', {
            'fields': ('content_type', 'object_id')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'action_taken', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = [
        'mark_as_reviewing',
        'mark_as_resolved',
        'mark_as_dismissed',
        'export_as_csv',
        'export_as_json'
    ]
    
    def report_type_badge(self, obj):
        """Display report type as colored badge."""
        colors = {
            'spam': '#ffc107',
            'harassment': '#dc3545',
            'hate_speech': '#dc3545',
            'violence': '#dc3545',
            'nudity': '#fd7e14',
            'false_info': '#17a2b8',
            'copyright': '#6c757d',
            'other': '#6c757d',
        }
        color = colors.get(obj.report_type, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_report_type_display()
        )
    report_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#ffc107',
            'reviewing': '#17a2b8',
            'resolved': '#28a745',
            'dismissed': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def content_preview(self, obj):
        """Display content preview."""
        preview = obj.get_content_preview()
        return preview[:50] + '...' if len(preview) > 50 else preview
    content_preview.short_description = 'Content'
    
    @admin.action(description='Mark as reviewing')
    def mark_as_reviewing(self, request, queryset):
        """Mark reports as under review."""
        updated = queryset.update(status='reviewing', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{updated} reports marked as reviewing.')
    
    @admin.action(description='Mark as resolved')
    def mark_as_resolved(self, request, queryset):
        """Mark reports as resolved."""
        updated = queryset.update(status='resolved', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{updated} reports marked as resolved.')
    
    @admin.action(description='Mark as dismissed')
    def mark_as_dismissed(self, request, queryset):
        """Mark reports as dismissed."""
        updated = queryset.update(status='dismissed', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{updated} reports dismissed.')


@admin.register(ModerationAction)
class ModerationActionAdmin(ExportMixin, admin.ModelAdmin):
    """
    Admin configuration for ModerationAction model.
    """
    list_display = ['id', 'moderator', 'action_type', 'target_user', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['moderator__username', 'target_user__username', 'reason']
    readonly_fields = ['moderator', 'created_at']
    date_hierarchy = 'created_at'
    actions = ['export_as_csv', 'export_as_json']
