from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import CustomUser, Profile, UserEmailVerification, PostMedia, Post, Comment, Hashtag, Notification, Wallet, Referral, Order, Payout
from .utils import send_verification_email, generate_video_thumbnail, extract_hashtags, extract_mentions, send_notification
from .tasks import process_post_media
import uuid

@receiver(post_save, sender=CustomUser)
def create_user_related_models(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            referral_code=uuid.uuid4().hex[:8].upper()
        )
        Wallet.objects.create(user=instance)
        UserEmailVerification.objects.create(user=instance)
        send_verification_email(instance)

@receiver(post_save, sender=CustomUser)
def save_user_related_models(sender, instance, **kwargs):
    instance.profile.save()
    if hasattr(instance, 'email_verification'):
        instance.email_verification.save()

@receiver(post_save, sender=PostMedia)
def create_post_media_thumbnail(sender, instance, created, **kwargs):
    if created and instance.media_type == 'video' and not instance.thumbnail:
        generate_video_thumbnail(instance)
    elif created and instance.media_type == 'image' and not instance.thumbnail:
        process_post_media.delay(instance.id)

def handle_hashtags(instance, text):
    tags = extract_hashtags(text)
    current_tags = set(instance.hashtags.values_list('name', flat=True))
    new_tags = set(tags)

    to_add = new_tags - current_tags
    to_remove = current_tags - new_tags

    for tag_name in to_remove:
        tag = Hashtag.objects.filter(name=tag_name).first()
        if tag:
            instance.hashtags.remove(tag)
            tag.count = max(0, tag.count - 1)
            tag.save()

    for tag_name in to_add:
        tag, created = Hashtag.objects.get_or_create(name=tag_name)
        instance.hashtags.add(tag)
        if not created:
            tag.count += 1
            tag.save()
        else:
            tag.count = 1
            tag.save()

def handle_mentions(instance, text):
    mentioned_usernames = extract_mentions(text)
    if not mentioned_usernames:
        return

    # Find users
    mentioned_users = CustomUser.objects.filter(username__in=mentioned_usernames)
    
    # Update M2M
    instance.mentions.set(mentioned_users)
    
    # Create notifications
    sender = instance.user
    for mentioned_user in mentioned_users:
        if mentioned_user != sender:
            kwargs = {
                'recipient': mentioned_user,
                'sender': sender,
                'notification_type': 'mention',
            }
            if isinstance(instance, Post):
                kwargs['post'] = instance
            else:
                kwargs['comment'] = instance
                kwargs['post'] = instance.post
            
            Notification.objects.get_or_create(**kwargs)

@receiver(post_save, sender=Post)
def process_post_content(sender, instance, **kwargs):
    handle_hashtags(instance, instance.caption)
    handle_mentions(instance, instance.caption)

@receiver(post_save, sender=Comment)
def process_comment_content(sender, instance, **kwargs):
    handle_hashtags(instance, instance.content)
    handle_mentions(instance, instance.content)

@receiver(post_save, sender=Order)
def handle_order_payout_and_referral(sender, instance, created, **kwargs):
    if instance.status == 'completed':
        # 1. Check for Referral Reward
        # Reward referrer when referred user makes their first sale
        seller = instance.seller
        referral = Referral.objects.filter(referred_user=seller, status='pending').first()
        if referral:
            # First sale detected for referred user
            # Reward referrer (e.g., 5.00 in virtual currency)
            reward = 5.00
            referral.status = 'rewarded'
            referral.reward_amount = reward
            referral.save()
            
            # Credit referrer's wallet
            referrer_wallet, _ = Wallet.objects.get_or_create(user=referral.referrer)
            referrer_wallet.balance += Decimal(str(reward))
            referrer_wallet.save()
            
            # Send notification
            send_notification(
                recipient=referral.referrer,
                sender=seller, # The user who made the sale
                notification_type='referral_reward'
            )
