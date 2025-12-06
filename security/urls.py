"""
URL configuration for security app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'2fa', views.TwoFactorAuthViewSet, basename='2fa')
router.register(r'2fa-login', views.Login2FAView, basename='2fa-login')

urlpatterns = [
    path('', include(router.urls)),
]
