import os
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import (
    Profile, Category, Listing, ListingMedia, Post, PostMedia, 
    SubscriptionPlan, Wallet, Follow, Conversation, Message, 
    Like, Comment, Story, Offer, Order, Review, Referral, 
    VirtualTransaction, FeatureFlag, DailyAggregate, Notification
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with extensive dummy data across all systems'

    def handle(self, *args, **kwargs):
        self.stdout.write("🏗️  Building high-fidelity dummy ecosystem...")

        # --- 1. CONFIG & SYSTEM ---
        FeatureFlag.objects.get_or_create(name="Dark Mode", defaults={"is_enabled": True})
        SubscriptionPlan.objects.update_or_create(name='Pro', defaults={'price': Decimal('9.99'), 'is_active': True})

        # --- 2. CATEGORIES ---
        tech, _ = Category.objects.update_or_create(slug='tech', defaults={'name': 'Technology', 'image': 'categories/tech.png'})

        # --- 3. USERS ---
        users_data = [
            ('admin', 'admin@chattingus.com', 'admin123', True),
            ('alex', 'alex@chattingus.com', 'alex123', False),
            ('sarah', 'sarah@chattingus.com', 'sarah123', False),
        ]
        users = {}
        credentials = []
        for uname, email, pwd, staff in users_data:
            user, created = User.objects.get_or_create(username=uname, defaults={'email': email, 'is_staff': staff, 'is_superuser': staff})
            if created:
                user.set_password(pwd)
                user.save()
            users[uname] = user
            credentials.append(f"User: {uname} | Pass: {pwd}")
            
            # Profile automation
            p = user.profile
            p.avatar = 'avatars/default_avatar.png'
            p.is_verified = True
            p.save()

        # --- 4. SOCIAL ---
        Follow.objects.get_or_create(follower=users['alex'], followed=users['admin'], status='accepted')
        
        post = Post.objects.create(user=users['admin'], caption="Hello World! #testing")
        PostMedia.objects.create(post=post, file='posts/post_lifestyle.png', media_type='image')
        Like.objects.create(user=users['alex'], post=post)
        Comment.objects.create(user=users['alex'], post=post, content="Nice post!")

        # --- 5. MARKETPLACE ---
        listing = Listing.objects.create(
            user=users['sarah'], category=tech, title='Pro Keyboard',
            description='Best keyboard in the world.', price=Decimal('99.00'), status='active'
        )
        ListingMedia.objects.create(listing=listing, file='listings/listing_product.png')
        
        order = Order.objects.create(
            listing=listing, buyer=users['alex'], seller=users['sarah'],
            amount=Decimal('99.00'), status='completed'
        )
        Review.objects.create(
            order=order, reviewer=users['alex'], reviewee=users['sarah'], 
            rating=5, item_as_described=5, communication=5, shipping_speed=5,
            comment="Perfect!"
        )

        # --- 6. CHAT ---
        conv = Conversation.objects.create(type='direct')
        conv.participants.add(users['admin'], users['alex'])
        Message.objects.create(conversation=conv, sender=users['admin'], text="Hi Alex!")

        # --- 7. WALLET ---
        w = users['admin'].wallet
        w.balance = Decimal('100.00')
        w.save()
        VirtualTransaction.objects.create(wallet=w, amount=Decimal('100.00'), transaction_type='credit', description='Bonus')

        # --- 8. REVIEWS & NOTIFICATIONS ---
        Notification.objects.create(recipient=users['admin'], sender=users['alex'], notification_type='like', post=post)

        # Output
        with open('users_list.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(credentials))

        self.stdout.write(self.style.SUCCESS("✅ Population Complete!"))
