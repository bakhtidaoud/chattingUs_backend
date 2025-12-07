# Admin Dashboard Integration Guide

## Quick Setup Instructions

### Step 1: Add to your main urls.py

Add these lines to your main `urls.py` file:

```python
from django.urls import path, include

urlpatterns = [
    # ... your existing URLs
    
    # Admin Dashboard URLs
    path('', include('admin_dashboard_urls')),
    
    # Mock API for testing (remove in production)
    path('api/', include('mock_api.mock_api_urls')),
]
```

### Step 2: Update CORS Settings

Add to your `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True
```

### Step 3: Access the Dashboard

1. **Start your Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Open your browser and go to**:
   ```
   http://localhost:8000/admin-dashboard/
   ```

3. **Login with any credentials** (mock API accepts anything):
   - Email: `admin@test.com`
   - Password: `password`

## What's Included

### ✅ Django Views (`admin_dashboard_views.py`)
- `AdminDashboardView` - Serves dashboard.html
- `AdminLoginView` - Serves login.html

### ✅ URL Configuration (`admin_dashboard_urls.py`)
- Dashboard pages routing
- Static files serving (CSS, JS, images)

### ✅ Mock API (`mock_api.py`)
- Authentication endpoints
- Dashboard analytics
- Users CRUD
- Posts list
- Stories list
- Security overview
- Settings management
- Reports/Moderation

## Mock API Endpoints

All endpoints accept requests without authentication for testing:

### Authentication
- `POST /api/auth/login/` - Login (accepts any credentials)
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/me/` - Current user

### Dashboard
- `GET /api/analytics/dashboard/` - Dashboard stats

### Users
- `GET /api/users/` - List users
- `GET /api/users/{id}/` - User detail

### Posts
- `GET /api/posts/` - List posts

### Stories
- `GET /api/stories/` - List stories

### Security
- `GET /api/security/overview/` - Security overview

### Settings
- `GET /api/settings/` - Get settings
- `PUT /api/settings/` - Update settings

### Moderation
- `GET /api/moderation/reports/` - List reports

## Next Steps

### For Production:

1. **Remove Mock API**: Delete or comment out the mock API URLs
2. **Implement Real API**: Create proper API endpoints in your Django app
3. **Add Authentication**: Implement JWT authentication
4. **Add Permissions**: Add proper permission checks
5. **Update API Base URL**: Change in `api.js` if needed

### Files to Modify:

1. **Main `urls.py`**: Add the admin dashboard URLs
2. **`settings.py`**: Update CORS and static files settings
3. **Create real API views**: Replace mock API with real implementations

## Troubleshooting

### CSS/JS not loading?
Make sure static files are being served correctly. Check your `STATIC_URL` in settings.py.

### API calls failing?
1. Check browser console for errors
2. Verify CORS settings
3. Make sure mock API URLs are included
4. Check that Django server is running

### Login not working?
The mock API accepts ANY credentials for testing. Just enter any email/password.

## File Structure

```
chattingUs_backend/
├── admin_dashboard_views.py (NEW)
├── admin_dashboard_urls.py (NEW)
├── mock_api.py (NEW)
├── admin-dashboard/
│   ├── dashboard.html
│   ├── login.html
│   ├── css/
│   │   ├── style.css
│   │   ├── responsive.css
│   │   └── ... (all CSS files)
│   └── js/
│       ├── api.js
│       ├── main.js
│       └── ... (all JS files)
└── urls.py (MODIFY THIS)
```

## Testing Checklist

- [ ] Dashboard loads at http://localhost:8000/admin-dashboard/
- [ ] Login page loads
- [ ] Can login with any credentials
- [ ] Dashboard shows mock data
- [ ] Navigation works between pages
- [ ] Responsive design works on mobile
- [ ] Dark mode toggle works
- [ ] All CSS/JS files load correctly

## Support

If you encounter any issues, check:
1. Django server is running
2. URLs are properly configured
3. CORS settings are correct
4. Browser console for JavaScript errors
5. Django logs for server errors
