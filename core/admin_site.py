from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from .models import DailyAggregate, CustomUser, Listing, Order, Category
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
import json

from django.http import JsonResponse

from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from .models import Report, Payout, PushNotification, Webhook
from django_celery_beat.models import PeriodicTask
import csv
import io
import requests

class CustomAdminSite(admin.AdminSite):
    site_header = "ChattingUS Administration"
    site_title = "ChattingUS Admin Portal"
    index_title = "Welcome to ChattingUS Admin"
    login_template = 'admin/login.html'
    index_template = 'admin/index.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('pending-moderation/', self.admin_view(self.pending_moderation_view), name='pending_moderation'),
            path('reports-management/', self.admin_view(self.reports_management_view), name='reports_management'),
            path('payouts-management/', self.admin_view(self.payouts_management_view), name='payouts_management'),
            path('push-notifications/', self.admin_view(self.push_notifications_view), name='push_notifications'),
            path('analytics/reports/', self.admin_view(self.reports_download_view), name='reports_download'),
            path('system/jobs/', self.admin_view(self.jobs_monitor_view), name='jobs_monitor'),
            path('profile/settings/', self.admin_view(self.profile_settings_view), name='profile_settings'),
            path('inventory/', self.admin_view(self.my_listings_view), name='my_listings'),
            path('system/audit-logs/', self.admin_view(self.audit_logs_view), name='audit_logs'),
            path('system/import-export/', self.admin_view(self.import_export_view), name='import_export'),
            path('system/webhooks/', self.admin_view(self.webhooks_management_view), name='webhooks_management'),
            path('system/webhooks/test/<int:webhook_id>/', self.admin_view(self.webhook_test_view), name='webhook_test'),
        ]
        return custom_urls + urls

    def profile_settings_view(self, request):
        if request.method == 'POST':
            # Logic for update, password change, etc.
            user = request.user
            user.bio = request.POST.get('bio')
            if 'avatar' in request.FILES:
                user.avatar = request.FILES['avatar']
            user.save()
            return JsonResponse({'status': 'success'})
        
        context = {
            **self.each_context(request),
            'title': 'User Settings',
            'user': request.user,
        }
        return TemplateResponse(request, "admin/profile_settings.html", context)

    def my_listings_view(self, request):
        status_filter = request.GET.get('status', 'active')
        listings = Listing.objects.filter(user=request.user, status=status_filter)
        context = {
            **self.each_context(request),
            'title': 'My Inventory',
            'listings': listings,
            'current_status': status_filter
        }
        return TemplateResponse(request, "admin/my_listings.html", context)

    def push_notifications_view(self, request):
        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')
            segment = request.POST.get('segment')
            scheduled_at = request.POST.get('scheduled_at')
            
            notification = PushNotification.objects.create(
                title=title,
                message=message,
                segment=segment,
                scheduled_at=scheduled_at or None,
                status='scheduled' if scheduled_at else 'sent',
                sent_at=timezone.now() if not scheduled_at else None
            )
            # Logic to trigger task would go here
            return JsonResponse({'status': 'success', 'id': notification.id})

        history = PushNotification.objects.all().order_by('-created_at')[:10]
        context = {
            **self.each_context(request),
            'title': 'Push Notifications',
            'history': history,
        }
        return TemplateResponse(request, "admin/push_notifications.html", context)

    def reports_download_view(self, request):
        # Daily/Weekly/Monthly report logic
        report_type = request.GET.get('type', 'daily')
        # Here we'd generate a PDF using reportlab or xhtml2pdf
        # For now, let's just show an HTML preview that can be printed
        today = timezone.now().date()
        aggregates = DailyAggregate.objects.all()[:30]
        context = {
            **self.each_context(request),
            'title': f'{report_type.title()} Performance Report',
            'report_type': report_type,
            'date': today,
            'aggregates': aggregates,
        }
        return TemplateResponse(request, "admin/reports_preview.html", context)

    def jobs_monitor_view(self, request):
        if request.method == 'POST':
            task_id = request.POST.get('task_id')
            action = request.POST.get('action') # 'run_now', 'enable', 'disable'
            try:
                task = PeriodicTask.objects.get(id=task_id)
                if action == 'enable': task.enabled = True
                elif action == 'disable': task.enabled = False
                task.save()
                return JsonResponse({'status': 'success'})
            except PeriodicTask.DoesNotExist:
                return JsonResponse({'status': 'error'}, status=404)

        tasks = PeriodicTask.objects.all()
        # Simulated queue length for demo
        queue_info = {
            'pending': 5,
            'active': 2,
            'failed': 1
        }
        context = {
            **self.each_context(request),
            'title': 'Background Jobs Monitor',
            'tasks': tasks,
            'queue_info': queue_info,
        }
        return TemplateResponse(request, "admin/jobs_monitor.html", context)

    def reports_management_view(self, request):
        if request.method == 'POST':
            report_id = request.POST.get('report_id')
            action = request.POST.get('action') # 'resolve', 'dismiss', 'investigate'
            try:
                report = Report.objects.get(id=report_id)
                if action == 'resolve':
                    report.status = 'resolved'
                elif action == 'dismiss':
                    report.status = 'dismissed'
                elif action == 'investigate':
                    report.status = 'investigating'
                elif action == 'escalate':
                    report.status = 'escalated'
                report.save()
                return JsonResponse({'status': 'success'})
            except Report.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Report not found'}, status=404)

        # Group reports by target object
        all_reports = Report.objects.filter(status__in=['pending', 'investigating', 'escalated']).order_by('-created_at')
        grouped_reports = {}
        for r in all_reports:
            key = f"{r.content_type.model}_{r.object_id}"
            if key not in grouped_reports:
                grouped_reports[key] = {
                    'target': r.content_object,
                    'type': r.content_type.model,
                    'reports': []
                }
            grouped_reports[key]['reports'].append(r)

        context = {
            **self.each_context(request),
            'title': 'Reports Management',
            'grouped_reports': grouped_reports.values(),
        }
        return TemplateResponse(request, "admin/reports_management.html", context)

    def payouts_management_view(self, request):
        if request.method == 'POST':
            payout_id = request.POST.get('payout_id')
            action = request.POST.get('action') # 'mark_paid'
            proof = request.FILES.get('proof')
            
            try:
                payout = Payout.objects.get(id=payout_id)
                if action == 'mark_paid':
                    payout.status = 'processed'
                    payout.proof_of_payment = proof
                    payout.processed_at = timezone.now()
                    payout.save()
                return JsonResponse({'status': 'success'})
            except Payout.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Payout not found'}, status=404)

        pending_payouts = Payout.objects.filter(status='requested').order_by('-created_at')
        context = {
            **self.each_context(request),
            'title': 'Seller Payouts',
            'payouts': pending_payouts,
        }
        return TemplateResponse(request, "admin/payouts_management.html", context)

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
        reports_count = Report.objects.filter(status='pending').count()
        payouts_count = Payout.objects.filter(status='requested').count()

        extra_context = extra_context or {}
        extra_context.update({
            'sales_data_json': json.dumps(sales_data),
            'user_growth_json': json.dumps(user_growth),
            'category_data_json': json.dumps(category_data),
            'total_revenue': total_revenue,
            'total_users': total_users,
            'active_listings': active_listings,
            'pending_moderation_count': pending_moderation_count,
            'reports_count': reports_count,
            'payouts_count': payouts_count,
        })
        return super().index(request, extra_context)

    def audit_logs_view(self, request):
        logs = LogEntry.objects.all().order_by('-action_time')
        
        # Filtering
        admin_id = request.GET.get('admin')
        if admin_id:
            logs = logs.filter(user_id=admin_id)
            
        action_flag = request.GET.get('action')
        if action_flag:
            logs = logs.filter(action_flag=action_flag)
            
        context = {
            **self.each_context(request),
            'logs': logs[:100],  # Limit to 100 for now
            'admins': CustomUser.objects.filter(is_staff=True),
            'title': "System Audit Logs"
        }
        return TemplateResponse(request, 'admin/audit_logs.html', context)

    def import_export_view(self, request):
        if request.method == 'POST' and 'import_users' in request.FILES:
            csv_file = request.FILES['import_users']
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            count = 0
            for row in reader:
                CustomUser.objects.get_or_create(
                    username=row['username'],
                    defaults={'email': row.get('email', ''), 'is_active': True}
                )
                count += 1
            return JsonResponse({'status': 'success', 'imported': count})

        context = {
            **self.each_context(request),
            'title': "Import / Export Data"
        }
        return TemplateResponse(request, 'admin/import_export.html', context)

    def webhooks_management_view(self, request):
        if request.method == 'POST':
            url = request.POST.get('url')
            event = request.POST.get('event')
            if url and event:
                Webhook.objects.create(url=url, event=event)
                
        webhooks = Webhook.objects.all().order_by('-created_at')
        context = {
            **self.each_context(request),
            'webhooks': webhooks,
            'title': "Webhook Management"
        }
        return TemplateResponse(request, 'admin/webhooks.html', context)

    def webhook_test_view(self, request, webhook_id):
        webhook = Webhook.objects.get(id=webhook_id)
        # Mocking a test payload
        payload = {'test': True, 'event': webhook.event, 'timestamp': timezone.now().isoformat()}
        try:
            response = requests.post(webhook.url, json=payload, timeout=5)
            status = 'success' if response.status_code < 400 else 'failed'
            msg = f"Response Code: {response.status_code}"
        except Exception as e:
            status = 'failed'
            msg = str(e)
            
        return JsonResponse({'status': status, 'message': msg})

custom_admin_site = CustomAdminSite(name='custom_admin')
