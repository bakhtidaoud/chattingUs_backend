"""
Admin Dashboard Views
Serves the admin dashboard HTML files
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
"""
Admin Dashboard Views
Serves the admin dashboard HTML files
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
import os


class AdminDashboardView(TemplateView):
    """
    Main admin dashboard view - serves the login page (index.html)
    """
    template_name = 'admin-dashboard/index.html'

    def get(self, request, *args, **kwargs):
        # Serve the login page (index.html)
        base_dir = os.path.dirname(__file__)
        
        login_path = os.path.join(base_dir, 'admin-dashboard', 'index.html')
        
        if os.path.exists(login_path):
            with open(login_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        
        return HttpResponse(f'Login page not found at: {login_path}', status=404)


class AdminLoginView(TemplateView):
    """
    Admin login page view - also serves index.html
    """
    template_name = 'admin-dashboard/index.html'

    def get(self, request, *args, **kwargs):
        # Serve the login HTML file
        base_dir = os.path.dirname(__file__)
        login_path = os.path.join(base_dir, 'admin-dashboard', 'index.html')
        
        if os.path.exists(login_path):
            with open(login_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        
        return HttpResponse('Login page not found', status=404)


class AdminDashboardPageView(TemplateView):
    """
    Admin dashboard page view - serves dashboard.html
    """
    template_name = 'admin-dashboard/dashboard.html'

    def get(self, request, *args, **kwargs):
        # Serve the dashboard HTML file
        base_dir = os.path.dirname(__file__)
        dashboard_path = os.path.join(base_dir, 'admin-dashboard', 'dashboard.html')
        
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        
        return HttpResponse('Dashboard page not found', status=404)


class AdminDebugView(TemplateView):
    """
    Debug page for troubleshooting
    """
    template_name = 'admin-dashboard/debug.html'

    def get(self, request, *args, **kwargs):
        # Serve the debug HTML file
        base_dir = os.path.dirname(__file__)
        debug_path = os.path.join(base_dir, 'admin-dashboard', 'debug.html')
        
        if os.path.exists(debug_path):
            with open(debug_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        
        return HttpResponse('Debug page not found', status=404)
