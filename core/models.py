from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AbstractUser
from taggit.managers import TaggableManager
import uuid
import os
from django.utils import timezone
from django.core.files.base import ContentFile

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]

    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='P')
    website = models.URLField(blank=True, null=True)
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_2fa_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    cover_photo = models.ImageField(upload_to='covers/', blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    interests = models.JSONField(default=list, blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

import uuid
from django.utils import timezone

class UserEmailVerification(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='email_verification')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Verification for {self.user.email}"

class SMSDevice(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='sms_device')
    phone_number = models.CharField(max_length=20)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)

    def is_valid(self):
        return self.otp_expiry and timezone.now() < self.otp_expiry

    def __str__(self):
        return f"SMS Device for {self.user.username}"

class Post(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    mentions = models.ManyToManyField(CustomUser, blank=True, related_name='mentioned_in')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager()
    hashtags = models.ManyToManyField('Hashtag', blank=True, related_name='posts')

    def __str__(self):
        return f"Post by {self.user.username} - {self.id}"

class PostMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='posts/')
    thumbnail = models.ImageField(upload_to='posts/thumbnails/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.media_type} for Post {self.post.id}"

class Like(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('love', 'Love'),
        ('haha', 'Haha'),
        ('wow', 'Wow'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type} to Post {self.post.id}"

class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    mentions = models.ManyToManyField(CustomUser, blank=True, related_name='comment_mentions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hashtags = models.ManyToManyField('Hashtag', blank=True, related_name='comments')

    def __str__(self):
        return f"Comment by {self.user.username} on Post {self.post.id}"

class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"#{self.name} ({self.count})"

class Follow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='followers')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='accepted')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.username} -> {self.followed.username} ({self.status})"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('follow_request', 'Follow Request'),
        ('follow_accept', 'Follow Accept'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('mention', 'Mention'),
        ('saved_search', 'Saved Search Match'),
    ]
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username} from {self.sender.username}"

class Block(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocking')
    blocked_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')

    def __str__(self):
        return f"{self.user.username} blocked {self.blocked_user.username}"

class Mute(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='muting')
    muted_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='muted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'muted_user')

    def __str__(self):
        return f"{self.user.username} muted {self.muted_user.username}"

class FeedPost(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feed_posts')
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    source = models.CharField(max_length=50, default='following') # 'following', 'suggested', etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'post')

    def __str__(self):
        return f"Feed entry for {self.user.username}: {self.post.id}"

class SavedCollection(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_collections')
    name = models.CharField(max_length=100)
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.user.username}'s Collection: {self.name}"

class SavedItem(models.Model):
    collection = models.ForeignKey(SavedCollection, on_delete=models.CASCADE, related_name='items')
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('collection', 'post')

    def __str__(self):
        return f"Post {self.post.id} in {self.collection.name}"

class Story(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='stories')
    media = models.FileField(upload_to='stories/')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Story by {self.user.username} - {self.id}"

class StoryView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'story')

    def __str__(self):
        return f"{self.user.username} viewed {self.story.id}"

class StoryReaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    emoji = models.CharField(max_length=20) # Storing emoji as string
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'story')

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to {self.story.id}"

class Highlight(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='highlights')
    name = models.CharField(max_length=100)
    cover_image = models.ImageField(upload_to='highlights/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Highlight: {self.name}"

class HighlightItem(models.Model):
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='items')
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('highlight', 'story')

    def __str__(self):
        return f"Story {self.story.id} in highlight {self.highlight.name}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    requires_approval = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Listing(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='listings')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='listings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejected_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    shipping_available = models.BooleanField(default=False)
    local_pickup = models.BooleanField(default=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_radius = models.PositiveIntegerField(null=True, blank=True, help_text="Delivery radius in km")

    def save(self, *args, **kwargs):
        if not self.id: # On creation
            # Set expiration to 30 days
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
            
            # Handle status based on category requirement
            if self.status == 'draft':
                pass # Keep as draft if user requested
            elif self.category and self.category.requires_approval:
                self.status = 'pending_review'
            else:
                self.status = 'active'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ListingPromotion(models.Model):
    PROMOTION_TYPES = [
        ('featured', 'Featured'),
        ('urgent', 'Urgent'),
    ]
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='promotions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPES)
    is_active = models.BooleanField(default=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def __str__(self):
        return f"{self.promotion_type} boost for {self.listing.title}"

class AttributeDefinition(models.Model):
    TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('select', 'Select'),
    ]
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='attribute_definitions')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class AttributeOption(models.Model):
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.value

class ListingAttributeValue(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE)
    value = models.TextField() # Storing all values as text

    class Meta:
        unique_together = ('listing', 'attribute')

    def __str__(self):
        return f"{self.listing.title} - {self.attribute.name}: {self.value}"

class SavedSearch(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('instant', 'Instant'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_searches')
    query = models.CharField(max_length=255, blank=True, null=True)
    filters = models.JSONField(default=dict, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    last_checked_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Search for {self.user.username}: {self.query or 'All'}"

class Conversation(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} with {self.participants.count()} participants"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} in Conv {self.conversation.id}"

class Offer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('countered', 'Countered'),
    ]
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='offers')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_offers')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    countered_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer of {self.amount} for {self.listing.title} by {self.buyer.username}"

class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('hate_speech', 'Hate Speech'),
        ('scam', 'Scam/Fraud'),
        ('other', 'Other'),
    ]
    reporter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reports_filed')
    
    # Generic Foreign Key to report anything (Post, Comment, User, Listing, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report by {self.reporter.username} - {self.reason} ({self.status})"

class Order(models.Model):
    DELIVERY_CHOICES = [
        ('shipping', 'Shipping'),
        ('pickup', 'Local Pickup'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, related_name='orders')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders_bought')
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders_sold')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_option = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} for {self.listing.title if self.listing else 'Deleted Listing'}"

class Dispute(models.Model):
    STATUS_CHOICES = [
        ('opened', 'Opened'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='disputes')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='disputes_created')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='opened')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispute for Order {self.order.id} by {self.created_by.username}"

class DisputeMessage(models.Model):
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} on Dispute {self.dispute.id}"
