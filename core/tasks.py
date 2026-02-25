from celery import shared_task
from django.utils import timezone
from .models import Story

@shared_task
def delete_expired_stories():
    expired_stories = Story.objects.filter(expires_at__lte=timezone.now())
    count = expired_stories.count()
    expired_stories.delete()
    return f"Deleted {count} expired stories"
