from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Profile, UserEmailVerification, PostMedia
from .utils import send_verification_email, generate_video_thumbnail

@receiver(post_save, sender=CustomUser)
def create_user_related_models(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
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
