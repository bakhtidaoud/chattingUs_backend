from django.db import models
from django.conf import settings

class Hashtag(models.Model):
    """
    Model for hashtags.
    """
    name = models.CharField(max_length=100, unique=True)
    posts_count = models.IntegerField(default=0)
    reels_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.name}"

class SearchHistory(models.Model):
    """
    Model for user search history.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Search histories'

    def __str__(self):
        return f"{self.user.username} searched for {self.query}"
