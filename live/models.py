"""
Models for live streaming functionality.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class LiveStream(models.Model):
    """
    Model for live streams.
    """
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('live', 'Live'),
        ('ended', 'Ended'),
    )
    
    streamer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_streams'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='live/thumbnails/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    viewer_count = models.IntegerField(default=0)
    peak_viewer_count = models.IntegerField(default=0)
    
    # Recording settings
    is_recorded = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True, null=True)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['streamer', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.streamer.username}'s live stream: {self.title}"
    
    def start_stream(self):
        """Start the live stream."""
        self.status = 'live'
        self.started_at = timezone.now()
        self.save()
    
    def end_stream(self):
        """End the live stream."""
        self.status = 'ended'
        self.ended_at = timezone.now()
        self.save()
        # Clean up all viewers
        self.viewers.all().delete()
    
    def update_viewer_count(self):
        """Update viewer count from active viewers."""
        count = self.viewers.filter(is_active=True).count()
        self.viewer_count = count
        if count > self.peak_viewer_count:
            self.peak_viewer_count = count
        self.save()
    
    @property
    def duration(self):
        """Get stream duration in seconds."""
        if self.started_at:
            end_time = self.ended_at or timezone.now()
            return (end_time - self.started_at).total_seconds()
        return 0


class LiveViewer(models.Model):
    """
    Model for tracking live stream viewers.
    """
    stream = models.ForeignKey(
        LiveStream,
        on_delete=models.CASCADE,
        related_name='viewers'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='viewing_streams'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['stream', 'user']
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['stream', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} viewing {self.stream.title}"
    
    def leave(self):
        """Mark viewer as inactive."""
        self.is_active = False
        self.left_at = timezone.now()
        self.save()


class LiveComment(models.Model):
    """
    Model for live stream comments.
    """
    stream = models.ForeignKey(
        LiveStream,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_comments'
    )
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['stream', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"


class LiveReaction(models.Model):
    """
    Model for live stream reactions (hearts, likes, etc.).
    """
    REACTION_TYPES = (
        ('heart', '❤️'),
        ('fire', '🔥'),
        ('clap', '👏'),
        ('laugh', '😂'),
        ('wow', '😮'),
    )
    
    stream = models.ForeignKey(
        LiveStream,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_reactions'
    )
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stream', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} reacted {self.get_reaction_type_display()}"
