"""
URL configuration for live streaming app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'streams', views.LiveStreamViewSet, basename='livestream')

urlpatterns = [
    path('', include(router.urls)),
]
