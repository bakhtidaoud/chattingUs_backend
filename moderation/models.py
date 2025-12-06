"""
Content moderation models.
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Report(models.Model):
    """
    Model for user-reported content.
    """
    REPORT_TYPES = (
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'),
        ('nudity', 'Nudity/Sexual Content'),
        ('false_info', 'False Information'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    # Reporter
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    
    # Reported content (generic relation)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Report details
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Review information
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.status}"
    
    def get_content_preview(self):
        """Get a preview of the reported content."""
        if self.content_object:
            if hasattr(self.content_object, 'caption'):
                return self.content_object.caption[:100]
            elif hasattr(self.content_object, 'text'):
                return self.content_object.text[:100]
            elif hasattr(self.content_object, 'username'):
                return f"User: {self.content_object.username}"
        return "Content not available"


class ModerationAction(models.Model):
    """
    Log of moderation actions taken.
    """
    ACTION_TYPES = (
        ('delete', 'Deleted Content'),
        ('ban_user', 'Banned User'),
        ('unban_user', 'Unbanned User'),
        ('warn_user', 'Warned User'),
        ('remove_content', 'Removed Content'),
        ('approve_content', 'Approved Content'),
        ('other', 'Other'),
    )
    
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='moderation_actions'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Target content (generic relation)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Target user (if applicable)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_actions_received'
    )
    
    reason = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Moderation Action'
        verbose_name_plural = 'Moderation Actions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} by {self.moderator}"
