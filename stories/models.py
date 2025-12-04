"""
Models for the stories app.
"""

from django.db import models
from django.conf import settings


class Story(models.Model):
    """
    Model for user stories (24-hour temporary content).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    image = models.ImageField(upload_to='stories/', null=True, blank=True)
    video = models.FileField(upload_to='stories/videos/', null=True, blank=True)
    text = models.TextField(max_length=500, blank=True)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'

    def __str__(self):
        return f"Story by {self.user.username} at {self.created_at}"


class StoryView(models.Model):
    """
    Model to track story views.
    """
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='story_views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'user')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.username} viewed {self.story}"
