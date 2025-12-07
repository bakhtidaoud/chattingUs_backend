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
    Main admin dashboard view
    """
    template_name = 'admin-dashboard/dashboard.html'

    def get(self, request, *args, **kwargs):
        # Serve the dashboard HTML file directly
        dashboard_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'admin-dashboard',
            'dashboard.html'
        )
        
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        
        return HttpResponse('Dashboard not found', status=404)


class AdminLoginView(TemplateView):
    """
    Admin login page view
    """
    template_name = 'admin-dashboard/login.html'

    def get(self, request, *args, **kwargs):
        # Serve the login HTML file directly
        login_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'admin-dashboard',
            'login.html'
        )
        
        if os.path.exists(login_path):
            with open(login_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        
        return HttpResponse('Login page not found', status=404)
