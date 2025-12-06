"""
URL configuration for posts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from . import comment_views

# Main router for posts
router = DefaultRouter()
router.register(r'', views.PostViewSet, basename='post')

# Nested router for comments under posts
posts_router = routers.NestedSimpleRouter(router, r'', lookup='post')
posts_router.register(r'comments', comment_views.CommentViewSet, basename='post-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(posts_router.urls)),
]
