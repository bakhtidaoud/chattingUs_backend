"""
URL configuration for reels app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.ReelViewSet, basename='reel')

urlpatterns = [
    path('', include(router.urls)),
]
