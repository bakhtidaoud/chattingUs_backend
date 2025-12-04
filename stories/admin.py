"""
Admin configuration for stories app.
"""

from django.contrib import admin
from .models import Story, StoryView


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'text', 'views_count', 'created_at', 'expires_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['user__username', 'text']


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'story', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__username']
