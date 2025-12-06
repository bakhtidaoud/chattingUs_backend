from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from posts.models import Post
from reels.models import Reel
from .models import Hashtag
from .utils import extract_hashtags

@receiver(post_save, sender=Post)
def update_post_hashtags(sender, instance, created, **kwargs):
    if created:
        tags = extract_hashtags(instance.caption)
        for tag in tags:
            hashtag, _ = Hashtag.objects.get_or_create(name=tag)
            hashtag.posts_count += 1
            hashtag.save()

@receiver(post_delete, sender=Post)
def remove_post_hashtags(sender, instance, **kwargs):
    tags = extract_hashtags(instance.caption)
    for tag in tags:
        try:
            hashtag = Hashtag.objects.get(name=tag)
            hashtag.posts_count = max(0, hashtag.posts_count - 1)
            hashtag.save()
        except Hashtag.DoesNotExist:
            pass

@receiver(post_save, sender=Reel)
def update_reel_hashtags(sender, instance, created, **kwargs):
    if created:
        tags = extract_hashtags(instance.caption)
        for tag in tags:
            hashtag, _ = Hashtag.objects.get_or_create(name=tag)
            hashtag.reels_count += 1
            hashtag.save()

@receiver(post_delete, sender=Reel)
def remove_reel_hashtags(sender, instance, **kwargs):
    tags = extract_hashtags(instance.caption)
    for tag in tags:
        try:
            hashtag = Hashtag.objects.get(name=tag)
            hashtag.reels_count = max(0, hashtag.reels_count - 1)
            hashtag.save()
        except Hashtag.DoesNotExist:
            pass
