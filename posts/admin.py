"""
Admin configuration for posts app.
"""

from django.contrib import admin
from .models import Post, Comment, Like


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['user', 'caption', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'caption']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'text', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'text']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username']
