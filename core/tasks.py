from celery import shared_task
from django.utils import timezone
from .models import Story, Listing, SavedSearch, Notification
from django.db.models import Q

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
