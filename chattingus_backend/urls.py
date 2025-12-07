"""
URL configuration for chattingus_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
import analytics_api
import users_api
import posts_api

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Admin Dashboard URLs
    path('', include('admin_dashboard_urls')),
    
    # Real Analytics API (takes precedence over mock)
    path('api/analytics/dashboard/', analytics_api.dashboard_stats, name='analytics_dashboard'),
    path('api/analytics/users/growth/', analytics_api.user_growth_stats, name='analytics_user_growth'),
    path('api/analytics/content/activity/', analytics_api.content_activity_stats, name='analytics_content_activity'),
    
    # Real Users API (takes precedence over mock)
    path('api/users/', users_api.users_list, name='users_list'),
    path('api/users/<int:pk>/', users_api.user_detail_or_update, name='user_detail'),
    path('api/users/<int:pk>/verify/', users_api.user_verify, name='user_verify'),
    
    # Real Posts API (takes precedence over mock)
    path('api/posts/', posts_api.posts_list, name='posts_list'),
    path('api/posts/<int:pk>/', posts_api.post_detail, name='post_detail'),
    
    # Mock API for testing (fallback for other endpoints)
    path('api/', include('mock_api')),
    
    # App URLs
    path('api/users/', include('users.urls')),
    path('api/posts/', include('posts.urls')),
    path('api/stories/', include('stories.urls')),
    path('api/reels/', include('reels.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/explore/', include('explore.urls')),
    path('api/media/', include('mediafiles.urls')),
    path('api/security/', include('security.urls')),
    path('api/live/', include('live.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema', template_name='api_docs.html'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
