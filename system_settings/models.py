"""
System settings and feature flags models.
"""

from django.db import models
from django.core.cache import cache
import json


class FeatureFlag(models.Model):
    """
    Feature flags for enabling/disabling features.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'
        ordering = ['name']
    
    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{status} {self.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Clear cache when feature flag changes
        cache.delete(f'feature_flag_{self.name}')
    
    @classmethod
    def is_feature_enabled(cls, name):
        """Check if a feature is enabled (with caching)."""
        cache_key = f'feature_flag_{name}'
        enabled = cache.get(cache_key)
        
        if enabled is None:
            try:
                flag = cls.objects.get(name=name)
                enabled = flag.is_enabled
                cache.set(cache_key, enabled, 300)  # Cache for 5 minutes
            except cls.DoesNotExist:
                enabled = False
        
        return enabled


class SystemSetting(models.Model):
    """
    System-wide settings.
    """
    SETTING_TYPES = (
        ('boolean', 'Boolean'),
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('json', 'JSON'),
    )
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    is_public = models.BooleanField(default=False, help_text='Can be accessed by non-admin users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key} = {self.get_display_value()}"
    
    def get_display_value(self):
        """Get formatted value for display."""
        if len(self.value) > 50:
            return self.value[:50] + '...'
        return self.value
    
    def get_typed_value(self):
        """Get value converted to appropriate type."""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.setting_type == 'integer':
            return int(self.value)
        elif self.setting_type == 'float':
            return float(self.value)
        elif self.setting_type == 'json':
            return json.loads(self.value)
        return self.value
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Clear cache when setting changes
        cache.delete(f'system_setting_{self.key}')
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value (with caching)."""
        cache_key = f'system_setting_{key}'
        value = cache.get(cache_key)
        
        if value is None:
            try:
                setting = cls.objects.get(key=key)
                value = setting.get_typed_value()
                cache.set(cache_key, value, 300)  # Cache for 5 minutes
            except cls.DoesNotExist:
                value = default
        
        return value


class MaintenanceMode(models.Model):
    """
    Maintenance mode settings.
    """
    is_enabled = models.BooleanField(default=False)
    message = models.TextField(
        default='System is currently under maintenance. Please check back later.'
    )
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    allowed_ips = models.JSONField(
        default=list,
        blank=True,
        help_text='List of IP addresses allowed during maintenance'
    )
    bypass_for_staff = models.BooleanField(
        default=True,
        help_text='Allow staff users to bypass maintenance mode'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Maintenance Mode'
        verbose_name_plural = 'Maintenance Mode'
    
    def __str__(self):
        status = "ACTIVE" if self.is_enabled else "Inactive"
        return f"Maintenance Mode: {status}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and MaintenanceMode.objects.exists():
            raise ValueError('Only one MaintenanceMode instance is allowed')
        super().save(*args, **kwargs)
        # Clear cache
        cache.delete('maintenance_mode')
    
    @classmethod
    def is_maintenance_active(cls):
        """Check if maintenance mode is active (with caching)."""
        cached = cache.get('maintenance_mode')
        if cached is None:
            try:
                mode = cls.objects.first()
                cached = mode.is_enabled if mode else False
                cache.set('maintenance_mode', cached, 60)  # Cache for 1 minute
            except:
                cached = False
        return cached
    
    @classmethod
    def get_instance(cls):
        """Get or create the maintenance mode instance."""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
