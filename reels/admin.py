"""
Admin configuration for reels app.
"""

from django.contrib import admin
from .models import Reel, ReelComment, ReelLike


@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = ['user', 'caption', 'likes_count', 'comments_count', 'views_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'caption']


@admin.register(ReelComment)
class ReelCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'reel', 'text', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'text']


@admin.register(ReelLike)
class ReelLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'reel', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
