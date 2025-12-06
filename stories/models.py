from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Story(models.Model):
    """
    Model for user stories (24-hour temporary content).
    """
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    media = models.FileField(upload_to='stories/', null=True, blank=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    text = models.TextField(max_length=500, blank=True)
    duration = models.IntegerField(default=5, help_text="Duration in seconds")
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(editable=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

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


class StoryHighlight(models.Model):
    """
    Model for story highlights (permanent collections of stories).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='highlights')
    title = models.CharField(max_length=100)
    cover = models.ImageField(upload_to='highlights/covers/', null=True, blank=True)
    stories = models.ManyToManyField(Story, related_name='highlights')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class StoryReply(models.Model):
    """
    Model for replies to stories.
    """
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='story_replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.user.username} to {self.story}"
