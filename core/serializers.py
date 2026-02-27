from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['cover_photo', 'occupation', 'interests', 'social_links', 'last_active', 'last_seen', 'is_online', 'dashboard_layout']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    seller_ratings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio', 'avatar', 'phone', 'location', 
                  'date_of_birth', 'gender', 'website', 'is_private', 'is_verified', 
                  'profile', 'followers_count', 'following_count', 'seller_ratings']

    def get_followers_count(self, obj):
        return obj.followers.filter(status='accepted').count()

    def get_following_count(self, obj):
        return obj.following.filter(status='accepted').count()

    def get_seller_ratings(self, obj):
        return obj.get_seller_ratings()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'referral_code']

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        if referral_code:
            try:
                referrer_profile = Profile.objects.get(referral_code=referral_code)
                profile = user.profile
                profile.referred_by = referrer_profile.user
                profile.save()
                Referral.objects.get_or_create(
                    referrer=referrer_profile.user,
                    referred_user=user
                )
            except Profile.DoesNotExist:
                pass
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializer(self.user)
        data['user'] = serializer.data
        return data

from rest_framework_simplejwt.serializers import TokenObtainSlidingSerializer

class CustomTokenObtainSlidingSerializer(TokenObtainSlidingSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializer(self.user)
        data['user'] = serializer.data
        return data

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

from .models import Post, PostMedia, Like, Comment, Hashtag
from taggit.serializers import TagListSerializerField, TaggitSerializer

class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name', 'count', 'created_at']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'reaction_type', 'created_at']
        read_only_fields = ['user']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    hashtags = HashtagSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'parent', 'content', 'mentions', 'hashtags', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['user']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'file', 'thumbnail', 'order', 'media_type']

class PostSerializer(TaggitSerializer, serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    tags = TagListSerializerField()
    hashtags = HashtagSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    reactions_counts = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'user', 'caption', 'location', 'mentions', 'tags', 'hashtags', 'media', 
                  'likes_count', 'reactions_counts', 'comments_count', 'created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_reactions_counts(self, obj):
        from django.db.models import Count
        reactions = obj.likes.values('reaction_type').annotate(count=Count('reaction_type'))
        return {r['reaction_type']: r['count'] for r in reactions}

    def get_comments_count(self, obj):
        return obj.comments.count()

from .models import Follow, Notification, NotificationSetting, Block, Mute, SavedCollection, SavedItem, Story, StoryView, StoryReaction, Highlight, HighlightItem, Category, Listing, AttributeDefinition, AttributeOption, ListingAttributeValue, ListingPromotion, SavedSearch, Conversation, Message, Offer, Report, Order, Dispute, DisputeMessage, Review, WishlistItem, SellerFollow, SubscriptionPlan, UserSubscription, Wallet, VirtualTransaction, Referral, Payout

class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    followed = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'followed', 'status', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'sender', 'notification_type', 'post', 'comment', 'is_read', 'created_at']
        read_only_fields = ['recipient', 'sender']

class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = ['id', 'type', 'email_enabled', 'push_enabled', 'in_app_enabled']

class BlockSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    blocked_user = UserSerializer(read_only=True)

    class Meta:
        model = Block
        fields = ['id', 'user', 'blocked_user', 'created_at']

class MuteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    muted_user = UserSerializer(read_only=True)

    class Meta:
        model = Mute
        fields = ['id', 'user', 'muted_user', 'created_at']

class SavedItemSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    
    class Meta:
        model = SavedItem
        fields = ['id', 'collection', 'post', 'created_at']

class SavedCollectionSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedCollection
        fields = ['id', 'user', 'name', 'is_private', 'items_count', 'created_at']
        read_only_fields = ['user']

    def get_items_count(self, obj):
        return obj.items.count()

class StorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    views_count = serializers.SerializerMethodField()
    is_viewed = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ['id', 'user', 'media', 'created_at', 'expires_at', 
                  'views_count', 'is_viewed', 'reactions_count', 'user_reaction']
        read_only_fields = ['user', 'expires_at']

    def get_views_count(self, obj):
        return obj.views.count()

    def get_is_viewed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.views.filter(user=request.user).exists()
        return False

    def get_reactions_count(self, obj):
        return obj.reactions.count()

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.emoji if reaction else None
        return None

class StoryViewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StoryView
        fields = ['id', 'user', 'story', 'viewed_at']

class StoryReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StoryReaction
        fields = ['id', 'user', 'story', 'emoji', 'created_at']

class HighlightItemSerializer(serializers.ModelSerializer):
    story = StorySerializer(read_only=True)

    class Meta:
        model = HighlightItem
        fields = ['id', 'highlight', 'story', 'created_at']

class HighlightSerializer(serializers.ModelSerializer):
    items = HighlightItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Highlight
        fields = ['id', 'user', 'name', 'cover_image', 'items', 'items_count', 'created_at']
        read_only_fields = ['user']

    def get_items_count(self, obj):
        return obj.items.count()

class AttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ['id', 'value']

class AttributeDefinitionSerializer(serializers.ModelSerializer):
    options = AttributeOptionSerializer(many=True, read_only=True)

    class Meta:
        model = AttributeDefinition
        fields = ['id', 'name', 'type', 'options']

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    attribute_definitions = AttributeDefinitionSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'parent', 'children', 'attribute_definitions', 'created_at']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.all(), many=True).data
        return []

class ListingAttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.ReadOnlyField(source='attribute.name')
    attribute_type = serializers.ReadOnlyField(source='attribute.type')

    class Meta:
        model = ListingAttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'attribute_type', 'value']

class ListingPromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingPromotion
        fields = ['id', 'listing', 'start_date', 'end_date', 'promotion_type', 'is_active', 'transaction_id', 'created_at']
        read_only_fields = ['user', 'is_active']

class ListingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    attribute_values = ListingAttributeValueSerializer(many=True, required=False)
    active_promotions = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'user', 'category', 'title', 'description', 'price', 'status', 
            'rejected_reason', 'expires_at', 'attribute_values', 'active_promotions', 
            'shipping_available', 'local_pickup', 'shipping_cost', 'delivery_radius',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'rejected_reason', 'expires_at']

    def get_active_promotions(self, obj):
        now = timezone.now()
        active = obj.promotions.filter(is_active=True, start_date__lte=now, end_date__gte=now)
        return ListingPromotionSerializer(active, many=True).data

    def create(self, validated_data):
        attribute_values_data = validated_data.pop('attribute_values', [])
        listing = Listing.objects.create(**validated_data)
        for attr_data in attribute_values_data:
            ListingAttributeValue.objects.create(listing=listing, **attr_data)
        return listing

    def update(self, instance, validated_data):
        attribute_values_data = validated_data.pop('attribute_values', None)
        instance = super().update(instance, validated_data)
        
        if attribute_values_data is not None:
            # Simple update: clear and recreate
            instance.attribute_values.all().delete()
            for attr_data in attribute_values_data:
                ListingAttributeValue.objects.create(listing=instance, **attr_data)
        
        return instance

class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = ['id', 'user', 'query', 'filters', 'frequency', 'alerts_enabled', 'last_checked_at', 'created_at']
        read_only_fields = ['user', 'last_checked_at']

from .models import MessageReaction

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'emoji', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'text', 'reactions', 'is_read', 'priority', 'attachment', 'created_at', 
                  'deleted_for_sender', 'deleted_for_receiver']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        
        if user:
            is_deleted = False
            if instance.sender == user and instance.deleted_for_sender:
                is_deleted = True
            elif instance.sender != user and instance.deleted_for_receiver:
                is_deleted = True
            
            if is_deleted:
                ret['text'] = None
                ret['is_deleted_for_me'] = True
        return ret

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    admins = UserSerializer(many=True, read_only=True)
    latest_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'admins', 'name', 'type', 'latest_message', 'created_at', 'updated_at']

    def get_latest_message(self, obj):
        message = obj.messages.last()
        if message:
            return MessageSerializer(message).data
        return None

class OfferSerializer(serializers.ModelSerializer):
    buyer_username = serializers.ReadOnlyField(source='buyer.username')
    listing_title = serializers.ReadOnlyField(source='listing.title')

    class Meta:
        model = Offer
        fields = ['id', 'listing', 'listing_title', 'buyer', 'buyer_username', 'amount', 'countered_amount', 'status', 'created_at', 'updated_at']
        read_only_fields = ['buyer', 'status', 'created_at', 'updated_at']

class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.ReadOnlyField(source='reporter.username')

    class Meta:
        model = Report
        fields = ['id', 'reporter', 'reporter_username', 'content_type', 'object_id', 'reason', 'description', 'status', 'created_at']
        read_only_fields = ['reporter', 'status', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    buyer_username = serializers.ReadOnlyField(source='buyer.username')
    seller_username = serializers.ReadOnlyField(source='seller.username')
    listing_title = serializers.ReadOnlyField(source='listing.title')

    class Meta:
        model = Order
        fields = [
            'id', 'listing', 'listing_title', 'buyer', 'buyer_username', 
            'seller', 'seller_username', 'amount', 'delivery_option', 
            'status', 'confirmed_at', 'payout_released', 'platform_fee',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['buyer', 'seller', 'amount', 'platform_fee', 'payout_released', 'confirmed_at', 'created_at', 'updated_at']

class DisputeMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = DisputeMessage
        fields = ['id', 'dispute', 'sender', 'sender_username', 'text', 'created_at']
        read_only_fields = ['sender', 'created_at']

class DisputeSerializer(serializers.ModelSerializer):
    creator_username = serializers.ReadOnlyField(source='created_by.username')
    messages = DisputeMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Dispute
        fields = ['id', 'order', 'created_by', 'creator_username', 'reason', 'status', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'status', 'created_at', 'updated_at']

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.ReadOnlyField(source='reviewer.username')
    reviewee_username = serializers.ReadOnlyField(source='reviewee.username')

    class Meta:
        model = Review
        fields = [
            'id', 'order', 'reviewer', 'reviewer_username', 
            'reviewee', 'reviewee_username', 'rating', 
            'item_as_described', 'communication', 'shipping_speed', 
            'comment', 'created_at'
        ]
        read_only_fields = ['reviewer', 'reviewee', 'created_at']

class WishlistItemSerializer(serializers.ModelSerializer):
    listing_title = serializers.ReadOnlyField(source='listing.title')
    
    class Meta:
        model = WishlistItem
        fields = ['id', 'user', 'listing', 'listing_title', 'created_at']
        read_only_fields = ['user']

class SellerFollowSerializer(serializers.ModelSerializer):
    seller_username = serializers.ReadOnlyField(source='seller.username')

    class Meta:
        model = SellerFollow
        fields = ['id', 'user', 'seller', 'seller_username', 'created_at']
        read_only_fields = ['user']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='plan.name')
    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'plan', 'plan_name', 'status', 'expires_at']
        read_only_fields = ['user', 'status', 'expires_at']

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance']
        read_only_fields = ['user', 'balance']

class VirtualTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualTransaction
        fields = '__all__'
        read_only_fields = ['wallet', 'created_at']

class ReferralSerializer(serializers.ModelSerializer):
    referrer_username = serializers.ReadOnlyField(source='referrer.username')
    referred_username = serializers.ReadOnlyField(source='referred_user.username')
    class Meta:
        model = Referral
        fields = ['id', 'referrer', 'referrer_username', 'referred_user', 'referred_username', 'reward_amount', 'status', 'created_at']

class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = '__all__'
        read_only_fields = ['user', 'status', 'stripe_payout_id', 'created_at']
