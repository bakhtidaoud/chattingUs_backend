# Django Backend Integration Guide for ChattingUs Admin Dashboard

## Required Django Packages

```bash
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-cors-headers
```

## Django Settings Configuration

### 1. Update `settings.py`

```python
INSTALLED_APPS = [
    # ... existing apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add this at the top
    # ... existing middleware
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your production frontend URL
]

CORS_ALLOW_CREDENTIALS = True

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

## Required API Endpoints

### 2. Create `urls.py` for API

```python
# urls.py (main)
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ... existing patterns
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/posts/', include('posts.urls')),
    path('api/comments/', include('comments.urls')),
    path('api/stories/', include('stories.urls')),
    path('api/live/', include('live.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/notifications/', include('notifications.urls')),
]
```

### 3. Authentication Endpoints (`authentication/urls.py`)

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

### 4. Login View (`authentication/views.py`)

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from users.serializers import UserSerializer

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is staff/admin
        if not user.is_staff and not user.is_superuser:
            return Response(
                {'error': 'Access denied. Admin privileges required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
```

### 5. User Endpoints (`users/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 6. User ViewSet (`users/views.py`)

```python
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']
```

### 7. User Serializer (`users/serializers.py`)

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'profile_picture', 'bio', 'is_active', 'is_staff',
            'date_joined', 'posts_count'
        ]
        read_only_fields = ['date_joined']
    
    def get_posts_count(self, obj):
        return obj.posts.count() if hasattr(obj, 'posts') else 0
```

### 8. Analytics Endpoints (`analytics/urls.py`)

```python
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('users/', views.UserAnalyticsView.as_view(), name='user-analytics'),
    path('posts/', views.PostAnalyticsView.as_view(), name='post-analytics'),
]
```

### 9. Analytics Views (`analytics/views.py`)

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from posts.models import Post
from comments.models import Comment
from stories.models import Story
from live.models import LiveStream

User = get_user_model()

class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        stats = {
            'total_users': User.objects.count(),
            'total_posts': Post.objects.count(),
            'total_comments': Comment.objects.count(),
            'active_live_streams': LiveStream.objects.filter(is_live=True).count(),
        }
        return Response(stats)

class UserAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Implement user analytics logic
        # Example: user growth over time
        return Response({
            'user_growth': [],  # Add your data
            'active_users': 0,
            'new_users_today': 0,
        })

class PostAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Implement post analytics logic
        return Response({
            'posts_today': 0,
            'total_likes': 0,
            'engagement_rate': 0,
        })
```

## Testing the Integration

### 1. Create a superuser

```bash
# Activate virtual environment first
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Create superuser
python manage.py createsuperuser
```

### 2. Run Django server

```bash
python manage.py runserver
```

### 3. Test API endpoints

```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "yourpassword"}'

# Test dashboard stats (with token)
curl -X GET http://localhost:8000/api/analytics/dashboard/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Update frontend API URL

Edit `admin-dashboard/js/api.js`:

```javascript
const API = {
    baseURL: 'http://localhost:8000/api',
    // ...
};
```

## Common Issues & Solutions

### Issue 1: CORS Errors

**Solution**: Make sure `corsheaders` is installed and configured correctly in `settings.py`

### Issue 2: 401 Unauthorized

**Solution**: 
- Check if user is staff/superuser
- Verify JWT token is being sent in headers
- Check token expiration

### Issue 3: Token Refresh Not Working

**Solution**: Make sure `SIMPLE_JWT` settings include `ROTATE_REFRESH_TOKENS: True`

### Issue 4: Search Not Working

**Solution**: Add `django-filter` package:
```bash
pip install django-filter
```

## Production Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Use environment variables for sensitive data
- [ ] Configure proper CORS origins
- [ ] Set up HTTPS
- [ ] Configure static files serving
- [ ] Set up database backups
- [ ] Enable logging
- [ ] Add rate limiting
- [ ] Configure caching
- [ ] Set up monitoring

## Environment Variables

Create `.env` file:

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## Next Steps

1. Implement all required models (Post, Comment, Story, LiveStream)
2. Create serializers for each model
3. Add pagination to list endpoints
4. Implement filtering and search
5. Add proper error handling
6. Write unit tests
7. Deploy to production

## Support

For issues or questions, refer to:
- Django REST Framework docs: https://www.django-rest-framework.org/
- SimpleJWT docs: https://django-rest-framework-simplejwt.readthedocs.io/
