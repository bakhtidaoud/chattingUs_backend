"""
Admin Dashboard URLs
URL configuration for admin dashboard
"""

from django.urls import path, include
from django.views.static import serve
from . import admin_dashboard_views
import os

# Get the admin-dashboard directory path
ADMIN_DASHBOARD_DIR = os.path.join(
    os.path.dirname(__file__),
    'admin-dashboard'
)

urlpatterns = [
    # Dashboard pages
    path('admin-dashboard/', admin_dashboard_views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-dashboard/login.html', admin_dashboard_views.AdminLoginView.as_view(), name='admin_login'),
    path('admin-dashboard/dashboard.html', admin_dashboard_views.AdminDashboardView.as_view(), name='admin_dashboard_page'),
    
    # Serve static files (CSS, JS, images)
    path('admin-dashboard/css/<path:path>', 
         lambda request, path: serve(request, path, document_root=os.path.join(ADMIN_DASHBOARD_DIR, 'css'))),
    path('admin-dashboard/js/<path:path>', 
         lambda request, path: serve(request, path, document_root=os.path.join(ADMIN_DASHBOARD_DIR, 'js'))),
    path('admin-dashboard/images/<path:path>', 
         lambda request, path: serve(request, path, document_root=os.path.join(ADMIN_DASHBOARD_DIR, 'images'))),
]
