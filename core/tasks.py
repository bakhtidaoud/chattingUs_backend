from celery import shared_task
from django.utils import timezone
from .models import Story, Listing, SavedSearch, Notification, DailyAggregate, Post, CustomUser, Order
from django.db.models import Q, Sum

@shared_task
def delete_expired_stories():
    expired_stories = Story.objects.filter(expires_at__lte=timezone.now())
    count = expired_stories.count()
    expired_stories.delete()
    return f"Deleted {count} expired stories"

@shared_task
def check_expired_listings():
    expired_listings = Listing.objects.filter(
        status='active',
        expires_at__lte=timezone.now()
    )
    count = expired_listings.count()
    expired_listings.update(status='expired')
    return f"Marked {count} listings as expired"

@shared_task
def process_saved_searches():
    searches = SavedSearch.objects.all()
    notifications_sent = 0
    
    for ss in searches:
        # Find active listings created after last check
        queryset = Listing.objects.filter(
            status='active', 
            created_at__gt=ss.last_checked_at
        )
        
        # Apply keyword search
        if ss.query:
            queryset = queryset.filter(
                Q(title__icontains=ss.query) | 
                Q(description__icontains=ss.query)
            )
        
        # Apply filters (e.g., category)
        if ss.filters:
            category_id = ss.filters.get('category')
            if category_id:
                queryset = queryset.filter(category_id=category_id)
            
            min_price = ss.filters.get('min_price')
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
                
            max_price = ss.filters.get('max_price')
            if max_price:
                queryset = queryset.filter(price__lte=max_price)

        # Notify if new listings found
        if queryset.exists():
            count = queryset.count()
            Notification.objects.create(
                recipient=ss.user,
                sender=ss.user, # System notification
                notification_type='saved_search',
                is_read=False
            )
            # In a real scenario, you'd send an email here too
            notifications_sent += 1
            
        # Update last check time
        ss.last_checked_at = timezone.now()
        ss.save()
        
    return f"Processed {searches.count()} searches, sent {notifications_sent} notifications"

from .models import CustomUser, Order

@shared_task
def send_missed_notification_digest(frequency='daily'):
    now = timezone.now()
    if frequency == 'daily':
        since = now - timezone.timedelta(days=1)
    else: # weekly
        since = now - timezone.timedelta(weeks=1)
        
    users = CustomUser.objects.filter(is_active=True)
    count = 0
    for user in users:
        unread_notifications = Notification.objects.filter(
            recipient=user,
            is_read=False,
            created_at__gte=since
        )
        
        if unread_notifications.exists():
            # In a real app, send actual email
            # send_mail(...)
            count += 1
            
    return f"Sent {frequency} digests to {count} users"

@shared_task
def auto_release_escrow():
    # Automatically release funds if buyer hasn't confirmed after 7 days of shipping
    RELEASE_DAYS = 7
    cutoff = timezone.now() - timezone.timedelta(days=RELEASE_DAYS)
    
    pending_orders = Order.objects.filter(
        status='shipped',
        updated_at__lte=cutoff,
        payout_released=False
    )
    
    count = 0
    for order in pending_orders:
        order.status = 'completed'
        order.payout_released = True
        order.confirmed_at = timezone.now()
        order.save()
        count += 1
        
    return f"Auto-released {count} orders"

@shared_task
def calculate_daily_aggregates():
    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    
    # Calculate metrics
    new_users = CustomUser.objects.filter(date_joined__date=yesterday).count()
    new_posts = Post.objects.filter(created_at__date=yesterday).count()
    new_listings = Listing.objects.filter(created_at__date=yesterday).count()
    new_orders = Order.objects.filter(created_at__date=yesterday).count()
    
    revenue = Order.objects.filter(
        created_at__date=yesterday, 
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Save aggregate
    DailyAggregate.objects.update_or_create(
        date=yesterday,
        defaults={
            'new_users': new_users,
            'new_posts': new_posts,
            'new_listings': new_listings,
            'new_orders': new_orders,
            'revenue': revenue
        }
    )
    
    return f"Calculated aggregates for {yesterday}"
