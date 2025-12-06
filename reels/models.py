"""
Models for the reels app.
"""

from django.db import models
from django.conf import settings


class Reel(models.Model):
    """
    Model for short-form video content (reels).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reels')
    video = models.FileField(upload_to='reels/')
    caption = models.TextField(max_length=2200, blank=True)
    thumbnail = models.ImageField(upload_to='reels/thumbnails/', null=True, blank=True)
    audio = models.CharField(max_length=100, blank=True, null=True)
    duration = models.IntegerField(default=0, help_text="Duration in seconds")
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reel by {self.user.username} at {self.created_at}"


class ReelComment(models.Model):
    """
    Model for reel comments.
    """
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reel_comments')
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.reel}"


class ReelLike(models.Model):
    """
    Model for reel likes.
    """
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reel_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reel', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} likes {self.reel}"
