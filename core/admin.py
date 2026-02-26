from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Post, PostMedia, SMSDevice, Like, Comment, Hashtag, Follow, Notification, Block, Mute, FeedPost, Story, StoryView, StoryReaction, Highlight, HighlightItem, Category, Listing, AttributeDefinition, AttributeOption, ListingAttributeValue, ListingPromotion, SavedSearch, Conversation, Message, Offer, Report, Order, Dispute, DisputeMessage, Review, WishlistItem, SellerFollow, SubscriptionPlan, UserSubscription, Wallet, VirtualTransaction, Referral, Payout, DailyAggregate, FeatureFlag
from django.contrib.admin.models import LogEntry
import uuid

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class PostMediaInline(admin.TabularInline):
    model = PostMedia
    extra = 1

class PostAdmin(admin.ModelAdmin):
    inlines = [PostMediaInline]
    list_display = ['user', 'caption', 'created_at']
    search_fields = ['caption', 'user__username']

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    inlines = (ProfileInline, )
    list_display = ['username', 'email', 'phone', 'location', 'is_staff', 'is_private']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('bio', 'avatar', 'phone', 'location', 'date_of_birth', 'gender', 'website', 'is_private')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('bio', 'avatar', 'phone', 'location', 'date_of_birth', 'gender', 'website', 'is_private')}),
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(Post, PostAdmin)
admin.site.register(SMSDevice)
admin.site.register(Like)
admin.site.register(Comment)

class HashtagAdmin(admin.ModelAdmin):
    list_display = ['name', 'count', 'created_at']
    search_fields = ['name']

admin.site.register(Hashtag, HashtagAdmin)

class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'followed', 'status', 'created_at']
    list_filter = ['status']

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']

admin.site.register(Follow, FollowAdmin)
admin.site.register(Notification, NotificationAdmin)

class BlockAdmin(admin.ModelAdmin):
    list_display = ['user', 'blocked_user', 'created_at']

class MuteAdmin(admin.ModelAdmin):
    list_display = ['user', 'muted_user', 'created_at']

admin.site.register(Block, BlockAdmin)
admin.site.register(Mute, MuteAdmin)

class FeedPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'source', 'created_at']
    list_filter = ['source']

admin.site.register(FeedPost, FeedPostAdmin)

class StoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at']
    list_filter = ['created_at', 'expires_at']

class StoryViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'story', 'viewed_at']

admin.site.register(Story, StoryAdmin)
admin.site.register(StoryView, StoryViewAdmin)

class StoryReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'story', 'emoji', 'created_at']

admin.site.register(StoryReaction, StoryReactionAdmin)

class HighlightItemInline(admin.TabularInline):
    model = HighlightItem
    extra = 1

class HighlightAdmin(admin.ModelAdmin):
    inlines = [HighlightItemInline]
    list_display = ['user', 'name', 'created_at']
    search_fields = ['name', 'user__username']

admin.site.register(Highlight, HighlightAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

admin.site.register(Category, CategoryAdmin)

class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 1

class AttributeDefinitionAdmin(admin.ModelAdmin):
    inlines = [AttributeOptionInline]
    list_display = ['name', 'category', 'type']
    list_filter = ['category', 'type']

admin.site.register(AttributeDefinition, AttributeDefinitionAdmin)

class ListingAttributeValueInline(admin.TabularInline):
    model = ListingAttributeValue
    extra = 1

class ListingPromotionInline(admin.TabularInline):
    model = ListingPromotion
    extra = 0

class OfferInline(admin.TabularInline):
    model = Offer
    extra = 0
    readonly_fields = ['buyer', 'amount', 'created_at']

class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    readonly_fields = ['buyer', 'amount', 'delivery_option', 'created_at']

class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingAttributeValueInline, ListingPromotionInline, OfferInline, OrderInline]
    list_display = ['title', 'user', 'category', 'status', 'price', 'created_at']
    list_filter = ['category', 'status', 'shipping_available', 'local_pickup', 'created_at']
    search_fields = ['title', 'description', 'user__username']

admin.site.register(Listing, ListingAdmin)

class ListingPromotionAdmin(admin.ModelAdmin):
    list_display = ['listing', 'user', 'promotion_type', 'start_date', 'end_date', 'is_active']
    list_filter = ['promotion_type', 'is_active', 'start_date']
    search_fields = ['listing__title', 'user__username', 'transaction_id']

admin.site.register(ListingPromotion, ListingPromotionAdmin)

class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'frequency', 'last_checked_at', 'created_at']
    list_filter = ['frequency', 'created_at']
    search_fields = ['user__username', 'query']

admin.site.register(SavedSearch, SavedSearchAdmin)

class MessageInline(admin.TabularInline):
    model = Message
    extra = 1

class ConversationAdmin(admin.ModelAdmin):
    inlines = [MessageInline]
    list_display = ['id', 'created_at', 'updated_at']

admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message)

class OfferAdmin(admin.ModelAdmin):
    list_display = ['listing', 'buyer', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['listing__title', 'buyer__username']

admin.site.register(Offer, OfferAdmin)

class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reason', 'content_object', 'status', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['reporter__username', 'description']
    actions = ['mark_as_investigating', 'mark_as_resolved', 'mark_as_dismissed']

    def mark_as_investigating(self, request, queryset):
        queryset.update(status='investigating')
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')

    def mark_as_dismissed(self, request, queryset):
        queryset.update(status='dismissed')

admin.site.register(Report, ReportAdmin)

class DisputeInline(admin.TabularInline):
    model = Dispute
    extra = 0
    readonly_fields = ['created_by', 'reason', 'status', 'created_at']

class ReviewInline(admin.StackedInline):
    model = Review
    extra = 0
    readonly_fields = ['reviewer', 'reviewee', 'rating', 'item_as_described', 'communication', 'shipping_speed', 'created_at']

class OrderAdmin(admin.ModelAdmin):
    inlines = [DisputeInline, ReviewInline]
    list_display = ['id', 'listing', 'buyer', 'seller', 'amount', 'delivery_option', 'status', 'payout_released', 'created_at']
    list_filter = ['status', 'delivery_option', 'payout_released', 'created_at']
    search_fields = ['listing__title', 'buyer__username', 'seller__username']
    actions = ['trigger_manual_payout']

    def trigger_manual_payout(self, request, queryset):
        count = 0
        for order in queryset.filter(status='completed', payout_released=False):
            # In a real app, call stripe.Payout.create(...)
            # mock payout
            Payout.objects.create(
                user=order.seller,
                order=order,
                amount=order.amount - order.platform_fee,
                status='processed',
                stripe_payout_id=f"po_{uuid.uuid4().hex[:12]}"
            )
            order.payout_released = True
            order.save()
            count += 1
        self.message_user(request, f"Triggered {count} payouts.")

admin.site.register(Order, OrderAdmin)

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']

class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'expires_at']
    list_filter = ['status', 'plan']

class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance']
    search_fields = ['user__username']

class VirtualTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'amount', 'transaction_type', 'created_at']
    list_filter = ['transaction_type', 'created_at']

class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']

class PayoutAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(VirtualTransaction, VirtualTransactionAdmin)
admin.site.register(Referral, ReferralAdmin)
admin.site.register(Payout, PayoutAdmin)

class DisputeMessageInline(admin.TabularInline):
    model = DisputeMessage
    extra = 1

class DisputeAdmin(admin.ModelAdmin):
    inlines = [DisputeMessageInline]
    list_display = ['id', 'order', 'created_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__listing__title', 'created_by__username', 'reason']
    actions = ['mark_as_under_review', 'mark_as_resolved', 'mark_as_closed']

    def mark_as_under_review(self, request, queryset):
        queryset.update(status='under_review')

    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved')

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')

admin.site.register(Dispute, DisputeAdmin)
admin.site.register(DisputeMessage)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['order', 'reviewer', 'reviewee', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['reviewer__username', 'reviewee__username', 'comment']

admin.site.register(Review, ReviewAdmin)

class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'listing', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'listing__title']

admin.site.register(WishlistItem, WishlistItemAdmin)

class SellerFollowAdmin(admin.ModelAdmin):
    list_display = ['user', 'seller', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'seller__username']

admin.site.register(SellerFollow, SellerFollowAdmin)

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['action_time', 'user', 'content_type', 'object_repr', 'action_flag']
    list_filter = ['action_flag', 'content_type', 'user']
    search_fields = ['object_repr', 'change_message']
    readonly_fields = ['action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(DailyAggregate)
class DailyAggregateAdmin(admin.ModelAdmin):
    list_display = ['date', 'new_users', 'new_posts', 'new_listings', 'new_orders', 'revenue']
    readonly_fields = ['date', 'new_users', 'new_posts', 'new_listings', 'new_orders', 'revenue']

@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_enabled', 'rollout_percentage']
    list_editable = ['is_enabled', 'rollout_percentage']
