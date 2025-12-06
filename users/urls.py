"""
URL configuration for users app - Enhanced with profile management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import profile_views
from . import social_views

router = DefaultRouter()
router.register(r'', views.UserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints (MUST BE BEFORE ROUTER)
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Password management - New endpoints for mobile app
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/verify-reset-token/<str:token>/', views.VerifyResetTokenView.as_view(), name='verify-reset-token'),
    path('auth/reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    
    # Password management - Legacy endpoints
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Verification
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify-email'),
    path('verify-phone/', views.PhoneVerificationView.as_view(), name='verify-phone'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend-verification'),
    
    # Social Authentication (Firebase - Google/Microsoft)
    path('auth/firebase/', social_views.firebase_auth, name='firebase-auth'),
    path('auth/link-social/', social_views.link_social_account_view, name='link-social'),
    path('auth/unlink-social/', social_views.unlink_social_account_view, name='unlink-social'),
    
    # Profile Management
    path('profile/', profile_views.ProfileManagementView.as_view(), name='profile'),
    path('profile/picture/', profile_views.ProfilePictureUploadView.as_view(), name='profile-picture'),
    path('search/', profile_views.UserSearchView.as_view(), name='user-search'),
    
    # Follow/Unfollow
    path('followers/', profile_views.FollowersListView.as_view(), name='followers-list'),
    path('following/', profile_views.FollowingListView.as_view(), name='following-list'),
    path('blocked/', profile_views.BlockedUsersListView.as_view(), name='blocked-users'),
    
    # User CRUD operations (includes /me/ and /<id>/)
    path('', include(router.urls)),
    
    # Integer-based paths (AFTER ROUTER, BEFORE USERNAME)
    path('<int:user_id>/follow/', profile_views.FollowUserView.as_view(), name='follow-user'),
    path('<int:user_id>/unfollow/', profile_views.UnfollowUserView.as_view(), name='unfollow-user'),
    path('<int:user_id>/block/', profile_views.BlockUserView.as_view(), name='block-user'),
    path('<int:user_id>/unblock/', profile_views.UnblockUserView.as_view(), name='unblock-user'),
    
    # Username pattern LAST (catches everything else)
    path('<str:username>/', profile_views.PublicProfileView.as_view(), name='public-profile'),
]
