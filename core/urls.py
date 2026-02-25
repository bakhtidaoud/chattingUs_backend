from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenRefreshSlidingView
from .views import (
    CustomTokenObtainPairView, CustomTokenObtainSlidingView, RegisterView, LogoutView, 
    PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView,
    VerifyEmailView, ResendVerificationView,
    EnableSMSView, VerifySMSView, Disable2FAView, StaticBackupCodesView,
    PostViewSet, CommentViewSet, HashtagViewSet, UserViewSet, FollowViewSet, NotificationViewSet,
    SavedCollectionViewSet, SavedItemViewSet, StoryViewSet, HighlightViewSet, CategoryViewSet,
    ListingViewSet, AttributeDefinitionViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'hashtags', HashtagViewSet, basename='hashtag')
router.register(r'users', UserViewSet, basename='user')
router.register(r'follows', FollowViewSet, basename='follow')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'collections', SavedCollectionViewSet, basename='collection')
router.register(r'saved-items', SavedItemViewSet, basename='saved-item')
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'highlights', HighlightViewSet, basename='highlight')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'listings', ListingViewSet, basename='listing')
router.register(r'attributes', AttributeDefinitionViewSet, basename='attribute')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/sliding/', CustomTokenObtainSlidingView.as_view(), name='token_obtain_sliding'),
    path('login/sliding/refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh_sliding'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('verify-email/resend/', ResendVerificationView.as_view(), name='resend_verification'),
    path('2fa/enable/', EnableSMSView.as_view(), name='enable_2fa'),
    path('2fa/verify/', VerifySMSView.as_view(), name='verify_2fa'),
    path('2fa/disable/', Disable2FAView.as_view(), name='disable_2fa'),
    path('2fa/backup-codes/', StaticBackupCodesView.as_view(), name='backup_codes'),
]
