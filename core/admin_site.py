from django_otp.admin import OTPAdminSite
from django.template.response import TemplateResponse
from django.urls import path
from .models import DailyAggregate, CustomUser, Listing, Order, Category
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
import json

from django.http import JsonResponse

class CustomAdminSite(OTPAdminSite):
    site_header = "ChattingUS Administration"
    site_title = "ChattingUS Admin Portal"
    index_title = "Welcome to ChattingUS Admin"
    login_template = 'admin/login.html'
    index_template = 'admin/index.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('pending-moderation/', self.admin_view(self.pending_moderation_view), name='pending_moderation'),
        ]
        return custom_urls + urls

    def pending_moderation_view(self, request):
        if request.method == 'POST':
            listing_id = request.POST.get('listing_id')
            action = request.POST.get('action')
            try:
                listing = Listing.objects.get(id=listing_id)
                if action == 'approve':
                    listing.status = 'active'
                    listing.save()
                elif action == 'reject':
                    listing.status = 'rejected'
                    listing.save()
                return JsonResponse({'status': 'success'})
            except Listing.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Listing not found'}, status=404)

        listings = Listing.objects.filter(status='pending_review').prefetch_related('media', 'user', 'category')
        context = {
            **self.each_context(request),
            'title': 'Pending Moderation',
            'listings': listings,
        }
        return TemplateResponse(request, "admin/pending_moderation.html", context)

    def index(self, request, extra_context=None):
        # Add analytics data to the context
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        # Sales Graph Data (Last 30 Days)
        aggregates = DailyAggregate.objects.filter(date__gte=last_30_days).order_by('date')
        sales_data = {
            'labels': [a.date.strftime('%Y-%m-%d') for a in aggregates],
            'values': [float(a.revenue) for a in aggregates]
        }

        # User Growth Data
        user_growth = {
            'labels': [a.date.strftime('%Y-%m-%d') for a in aggregates],
            'values': [a.new_users for a in aggregates]
        }

        # Listing Categories Donut
        categories = Category.objects.annotate(listing_count=Count('listings')).filter(listing_count__gt=0)
        category_data = {
            'labels': [c.name for c in categories],
            'values': [c.listing_count for c in categories]
        }

        # Quick Stats for Cards
        total_revenue = Order.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        total_users = CustomUser.objects.count()
        active_listings = Listing.objects.filter(status='active').count()
        pending_moderation_count = Listing.objects.filter(status='pending_review').count()

        extra_context = extra_context or {}
        extra_context.update({
            'sales_data_json': json.dumps(sales_data),
            'user_growth_json': json.dumps(user_growth),
            'category_data_json': json.dumps(category_data),
            'total_revenue': total_revenue,
            'total_users': total_users,
            'active_listings': active_listings,
            'pending_moderation_count': pending_moderation_count,
        })
        return super().index(request, extra_context)

custom_admin_site = CustomAdminSite(name='custom_admin')
