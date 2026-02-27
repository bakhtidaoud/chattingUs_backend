from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
import random
import uuid
from decimal import Decimal
from django.utils import timezone
from .models import CustomUser, UserEmailVerification, SMSDevice, Post, PostMedia, Like, Comment, Hashtag, Follow, Notification, Block, Mute, FeedPost, SavedCollection, SavedItem, Story, StoryView, StoryReaction, Highlight, HighlightItem, Category, Listing, AttributeDefinition, ListingAttributeValue, ListingPromotion, SavedSearch, Conversation, Message, Offer, Report, Order, Dispute, DisputeMessage, Review, WishlistItem, SellerFollow, ListingView
from .utils import send_verification_email, send_sms, send_notification
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth import get_user_model
from .throttles import AuthRateThrottle, PostRateThrottle, MarketplaceRateThrottle, VerifiedUserRateThrottle
from .serializers import (
    RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer, 
    CustomTokenObtainSlidingSerializer, PasswordChangeSerializer,
    PostSerializer, PostMediaSerializer, LikeSerializer, CommentSerializer,
    HashtagSerializer, FollowSerializer, NotificationSerializer,
    BlockSerializer, MuteSerializer,
    SavedCollectionSerializer, SavedItemSerializer,
    StorySerializer, StoryViewSerializer, StoryReactionSerializer,
    HighlightSerializer, CategorySerializer,
    AttributeDefinitionSerializer, ListingSerializer, ListingPromotionSerializer,
    SavedSearchSerializer, ConversationSerializer, MessageSerializer, OfferSerializer,
    ReportSerializer, OrderSerializer, DisputeSerializer, DisputeMessageSerializer,
    ReviewSerializer, WishlistItemSerializer, SellerFollowSerializer,
    NotificationSettingSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer,
    WalletSerializer, VirtualTransactionSerializer, ReferralSerializer, PayoutSerializer
)
from .models import (
    CustomUser, Profile, Follow, Notification, NotificationSetting, SubscriptionPlan, 
    UserSubscription, Wallet, VirtualTransaction, Referral, Payout, Order, Review
)
from rest_framework import viewsets
from rest_framework.decorators import action
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from rest_framework_simplejwt.views import TokenObtainSlidingView

class CustomTokenObtainSlidingView(TokenObtainSlidingView):
    serializer_class = CustomTokenObtainSlidingSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data.get('old_password')):
                user.set_password(serializer.validated_data.get('new_password'))
                user.save()
                update_session_auth_hash(request, user)
                return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Incorrect old password.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'If an account exists with this email, a reset link has been sent.'}, status=status.HTTP_200_OK)

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"http://localhost:3000/reset-password/{uid}/{token}/"  # Placeholder UI URL
        
        send_mail(
            'Password Reset Request',
            f'Click the link to reset your password: {reset_url}',
            settings.DEFAULT_FROM_EMAIL or 'noreply@chattingus.com',
            [email],
            fail_silently=False,
        )
        return Response({'message': 'If an account exists with this email, a reset link has been sent.'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.data.get('new_password')
            if not new_password:
                return Response({'error': 'New password is required.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            verification = UserEmailVerification.objects.get(token=token)
            if verification.is_expired():
                return Response({'error': 'Token has expired.'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = verification.user
            user.is_verified = True
            user.save()
            
            # Optionally delete token after verification
            verification.delete()
            
            return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        except UserEmailVerification.DoesNotExist:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({'message': 'Email is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update token or create new one
            verification, created = UserEmailVerification.objects.get_or_create(user=user)
            if not created:
                verification.token = uuid.uuid4()
                verification.expires_at = timezone.now() + timezone.timedelta(hours=24)
                verification.save()
            
            send_verification_email(user)
            return Response({'message': 'Verification email resent.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'If an account exists with this email, a verification link has been sent.'}, status=status.HTTP_200_OK)

class EnableSMSView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        device, created = SMSDevice.objects.get_or_create(user=request.user)
        device.phone_number = phone_number
        device.otp_code = str(random.randint(100000, 999999))
        device.otp_expiry = timezone.now() + timezone.timedelta(minutes=5)
        device.is_confirmed = False
        device.save()
        
        send_sms(phone_number, f"Your ChattingUs verification code is: {device.otp_code}")
        return Response({'message': 'Verification code sent to your phone.'}, status=status.HTTP_200_OK)

class VerifySMSView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        code = request.data.get('code')
        try:
            device = request.user.sms_device
            if device.otp_code == code and device.is_valid():
                device.is_confirmed = True
                device.save()
                
                user = request.user
                user.is_2fa_enabled = True
                user.save()
                
                # Generate static backup codes if they don't exist
                static_device, created = StaticDevice.objects.get_or_create(user=user, name='backup-codes')
                if created:
                    for _ in range(10):
                        token = str(random.randint(10000000, 99999999))
                        StaticToken.objects.create(device=static_device, token=token)
                
                return Response({'message': '2FA enabled successfully.'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)
        except SMSDevice.DoesNotExist:
            return Response({'error': 'No SMS device found.'}, status=status.HTTP_400_BAD_REQUEST)

class Disable2FAView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        user.is_2fa_enabled = False
        user.save()
        
        if hasattr(user, 'sms_device'):
            user.sms_device.delete()
            
        StaticDevice.objects.filter(user=user).delete()
        
        return Response({'message': '2FA disabled successfully.'}, status=status.HTTP_200_OK)

class StaticBackupCodesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        try:
            device = StaticDevice.objects.get(user=request.user, name='backup-codes')
            tokens = StaticToken.objects.filter(device=device).values_list('token', flat=True)
            return Response({'backup_codes': tokens}, status=status.HTTP_200_OK)
        except StaticDevice.DoesNotExist:
            return Response({'error': 'No backup codes found.'}, status=status.HTTP_400_BAD_REQUEST)

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [PostRateThrottle, VerifiedUserRateThrottle]

    @method_decorator(cache_page(60 * 15)) # Cache for 15 mins
    def list(self, request, *args, **kwargs):
        # Only cache for anonymous users to avoid mixing personalized feeds
        if not request.user.is_authenticated:
            return super().list(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.all().order_by('-created_at')
        
        # Search query
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(search_vector=search_query)

        if user.is_authenticated:
            # Exclude posts from blocked users and users who blocked me
            blocked_users = Block.objects.filter(user=user).values_list('blocked_user', flat=True)
            blocked_by_users = Block.objects.filter(blocked_user=user).values_list('user', flat=True)
            # Exclude posts from muted users
            muted_users = Mute.objects.filter(user=user).values_list('muted_user', flat=True)
            
            queryset = queryset.exclude(user__in=blocked_users)
            queryset = queryset.exclude(user__in=blocked_by_users)
            queryset = queryset.exclude(user__in=muted_users)
        return queryset

    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        
        # Handle media files if any
        files = self.request.FILES.getlist('media_files')
        for i, file in enumerate(files):
            # Simple detection of media type
            media_type = 'video' if file.content_type.startswith('video') else 'image'
            PostMedia.objects.create(
                post=post,
                file=file,
                order=i,
                media_type=media_type
            )
        
        # Tags are handled by TaggitSerializer automaticaly if present in data

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        post = self.get_object()
        reaction_type = request.data.get('reaction_type', 'like')
        
        valid_reactions = [choice[0] for choice in Like.REACTION_CHOICES]
        if reaction_type not in valid_reactions:
            return Response({'error': f'Invalid reaction type. Choose from: {", ".join(valid_reactions)}'}, 
                            status=status.HTTP_400_BAD_REQUEST)
            
        like, created = Like.objects.get_or_create(
            user=request.user, 
            post=post,
            defaults={'reaction_type': reaction_type}
        )
        
        if not created:
            if like.reaction_type == reaction_type:
                like.delete()
                return Response({'status': 'reaction removed'}, status=status.HTTP_200_OK)
            else:
                like.reaction_type = reaction_type
                like.save()
                return Response({'status': 'reaction updated'}, status=status.HTTP_200_OK)
        
        # Notify post owner
        if post.user != request.user:
            send_notification(
                recipient=post.user,
                sender=request.user,
                notification_type='like',
                post=post
            )
                
        return Response({'status': 'reaction added'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        # Fetch only top-level comments; replies are nested via serializer
        comments = post.comments.filter(parent=None).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def save(self, request, pk=None):
        post = self.get_object()
        collection_id = request.data.get('collection_id')
        
        # Default to "All Saved" collection if not specified
        if not collection_id:
            collection, created = SavedCollection.objects.get_or_create(
                user=request.user,
                name='All Saved',
                defaults={'is_private': True}
            )
        else:
            try:
                collection = SavedCollection.objects.get(id=collection_id, user=request.user)
            except SavedCollection.DoesNotExist:
                return Response({'error': 'Collection not found'}, status=status.HTTP_404_NOT_FOUND)
        
        saved_item, created = SavedItem.objects.get_or_create(collection=collection, post=post)
        if not created:
            saved_item.delete()
            return Response({'status': 'unsaved'}, status=status.HTTP_200_OK)
            
        return Response({'status': 'saved'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def feed(self, request):
        user = request.user
        # Get post IDs from pre-computed feed
        feed_posts = FeedPost.objects.filter(user=user).values_list('post_id', flat=True)
        posts = Post.objects.filter(id__in=feed_posts).order_by('-created_at')
        
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_hashtag(self, request):
        hashtag_name = request.query_params.get('hashtag')
        if not hashtag_name:
            return Response({'error': 'hashtag query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        posts = self.queryset.filter(hashtags__name=hashtag_name)
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)

class HashtagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Hashtag.objects.all().order_by('-count')
    serializer_class = HashtagSerializer

    @action(detail=False, methods=['get'])
    def trending(self, request):
        trending_tags = self.queryset.filter(count__gt=0)[:10]
        serializer = self.get_serializer(trending_tags, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = Comment.objects.all()
        if user.is_authenticated:
            blocked_users = Block.objects.filter(user=user).values_list('blocked_user', flat=True)
            blocked_by_users = Block.objects.filter(blocked_user=user).values_list('user', flat=True)
            queryset = queryset.exclude(user__in=blocked_users).exclude(user__in=blocked_by_users)
        return queryset

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        if comment.post.user != self.request.user:
            send_notification(
                recipient=comment.post.user,
                sender=self.request.user,
                notification_type='comment',
                post=comment.post,
                comment=comment
            )

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [AuthRateThrottle, VerifiedUserRateThrottle]

    def retrieve(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        cache_key = f'user_profile_{user_id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600) # 1 hour
        return response

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def onboard_stripe(self, request):
        user = request.user
        # Generate mock Stripe Connect link
        account_id = f"acct_{random.getrandbits(32)}"
        user.profile.stripe_account_id = account_id
        user.profile.save()
        return Response({
            'stripe_url': f"https://connect.stripe.com/express/oauth/authorize?client_id=ca_123&state={account_id}",
            'account_id': account_id
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def stripe_callback(self, request):
        user = request.user
        user.profile.is_onboarded = True
        user.profile.save()
        return Response({'status': 'seller onboarded'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        target_user = self.get_object()
        if target_user == request.user:
            return Response({'error': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        
        status_follow = 'pending' if target_user.is_private else 'accepted'
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            followed=target_user,
            defaults={'status': status_follow}
        )
        
        if not created:
            follow.delete()
            return Response({'status': 'unfollowed'}, status=status.HTTP_200_OK)
        
        if status_follow == 'pending':
            send_notification(
                recipient=target_user,
                sender=request.user,
                notification_type='follow_request'
            )
            return Response({'status': 'requested'}, status=status.HTTP_201_CREATED)
        else:
            send_notification(
                recipient=target_user,
                sender=request.user,
                notification_type='follow_accept'
            )
            return Response({'status': 'followed'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def block(self, request, pk=None):
        target_user = self.get_object()
        if target_user == request.user:
            return Response({'error': 'You cannot block yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        
        block, created = Block.objects.get_or_create(user=request.user, blocked_user=target_user)
        if not created:
            block.delete()
            return Response({'status': 'unblocked'}, status=status.HTTP_200_OK)
        
        # Also unfollow automatically if blocking
        Follow.objects.filter(follower=request.user, followed=target_user).delete()
        Follow.objects.filter(follower=target_user, followed=request.user).delete()
        
        return Response({'status': 'blocked'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mute(self, request, pk=None):
        target_user = self.get_object()
        if target_user == request.user:
            return Response({'error': 'You cannot mute yourself.'}, status=status.HTTP_400_BAD_REQUEST)
        
        mute, created = Mute.objects.get_or_create(user=request.user, muted_user=target_user)
        if not created:
            mute.delete()
            return Response({'status': 'unmuted'}, status=status.HTTP_200_OK)
        
        return Response({'status': 'muted'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def suggested(self, request):
        from django.db.models import Count
        user = request.user
        my_following = Follow.objects.filter(follower=user, status='accepted').values_list('followed_id', flat=True)
        blocked_ids = Block.objects.filter(user=user).values_list('blocked_user_id', flat=True)
        blocked_by_ids = Block.objects.filter(blocked_user=user).values_list('user_id', flat=True)
        
        exclude_ids = list(my_following) + [user.id] + list(blocked_ids) + list(blocked_by_ids)
        
        # 1. Mutual Follows (People followed by people I follow)
        mutual_follow_candidates = Follow.objects.filter(
            follower_id__in=my_following,
            status='accepted'
        ).exclude(followed_id__in=exclude_ids).values('followed_id').annotate(mutual_count=Count('followed_id'))
        
        # 2. Location matches
        location_candidates = User.objects.filter(
            location__iexact=user.location
        ).exclude(id__in=exclude_ids).values_list('id', flat=True) if user.location else []
        
        # Merge all candidates
        candidate_ids = set([c['followed_id'] for c in mutual_follow_candidates])
        candidate_ids.update(location_candidates)
        
        # If very few candidates, add some random active users
        if len(candidate_ids) < 10:
            random_users = User.objects.filter(is_active=True).exclude(id__in=exclude_ids).order_by('?')[:10]
            candidate_ids.update([u.id for u in random_users])
            
        users_qset = User.objects.filter(id__in=candidate_ids).select_related('profile')
        
        suggestions = []
        my_interests = set(user.profile.interests) if hasattr(user, 'profile') else set()
        mutual_counts = {c['followed_id']: c['mutual_count'] for c in mutual_follow_candidates}
        
        for potential in users_qset:
            score = 0
            reasons = []
            
            # Mutuals factor
            m_count = mutual_counts.get(potential.id, 0)
            if m_count > 0:
                score += m_count * 10
                reasons.append(f"Followed by {m_count} people you follow")
            
            # Location factor
            if user.location and potential.location and potential.location.lower() == user.location.lower():
                score += 8
                reasons.append(f"Living in {user.location}")
                
            # Interests factor
            if hasattr(potential, 'profile'):
                pot_interests = set(potential.profile.interests)
                common = my_interests.intersection(pot_interests)
                if common:
                    score += len(common) * 5
                    reasons.append(f"Shared interests: {', '.join(list(common)[:2])}")
            
            if score > 0 or not suggestions: # include at least some if empty
                suggestions.append({
                    'user': UserSerializer(potential).data,
                    'score': score,
                    'reasons': reasons
                })
        
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply pagination to the raw list
        page = self.paginate_queryset(suggestions)
        if page is not None:
             return self.get_paginated_response(page)
        
        return Response(suggestions)

class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        follow = self.get_object()
        if follow.followed != request.user:
            return Response({'error': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        
        follow.status = 'accepted'
        follow.save()
        
        Notification.objects.create(
            recipient=follow.follower,
            sender=request.user,
            notification_type='follow_accept'
        )
        return Response({'status': 'accepted'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        follow = self.get_object()
        if follow.followed != request.user:
            return Response({'error': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        
        follow.status = 'rejected'
        follow.save()
        return Response({'status': 'rejected'})

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked as read'})

    @action(detail=False, methods=['post'])
    def clear_all(self, request):
        self.get_queryset().delete()
        return Response({'status': 'all notifications cleared'})

class NotificationSettingViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSettingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationSetting.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SavedCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = SavedCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedCollection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SavedItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SavedItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedItem.objects.filter(collection__user=self.request.user)

class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Only show active stories (non-expired)
        return Story.objects.filter(expires_at__gt=timezone.now()).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def record_view(self, request, pk=None):
        story = self.get_object()
        if story.user == request.user:
            return Response({'status': 'own story'}, status=status.HTTP_200_OK)
            
        view, created = StoryView.objects.get_or_create(user=request.user, story=story)
        return Response({'status': 'view recorded'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def following_stories(self, request):
        # Get stories only from people I follow
        following_ids = Follow.objects.filter(
            follower=request.user, 
            status='accepted'
        ).values_list('followed_id', flat=True)
        
        stories = self.get_queryset().filter(user_id__in=following_ids)
        serializer = self.get_serializer(stories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def react(self, request, pk=None):
        story = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response({'error': 'Emoji is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        reaction, created = StoryReaction.objects.get_or_create(
            user=request.user, 
            story=story,
            defaults={'emoji': emoji}
        )
        
        if not created:
            if reaction.emoji == emoji:
                reaction.delete()
                return Response({'status': 'reaction removed'}, status=status.HTTP_200_OK)
            else:
                reaction.emoji = emoji
                reaction.save()
                return Response({'status': 'reaction updated'}, status=status.HTTP_200_OK)
                
        return Response({'status': 'reaction added'}, status=status.HTTP_201_CREATED)

class HighlightViewSet(viewsets.ModelViewSet):
    serializer_class = HighlightSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return Highlight.objects.filter(user_id=user_id)
        return Highlight.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_story(self, request, pk=None):
        highlight = self.get_object()
        if highlight.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
            
        story_id = request.data.get('story_id')
        try:
            story = Story.objects.get(id=story_id)
            if story.user != request.user:
                return Response({'error': 'Can only add your own stories to highlights'}, status=status.HTTP_400_BAD_REQUEST)
        except Story.DoesNotExist:
            return Response({'error': 'Story not found'}, status=status.HTTP_404_NOT_FOUND)
            
        item, created = HighlightItem.objects.get_or_create(highlight=highlight, story=story)
        if not created:
            item.delete()
            return Response({'status': 'story removed from highlight'}, status=status.HTTP_200_OK)
            
        return Response({'status': 'story added to highlight'}, status=status.HTTP_201_CREATED)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @method_decorator(cache_page(60 * 60 * 24)) # Cache for 24 hours
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        # Allow filtering to get only top-level (root) categories
        roots_only = self.request.query_params.get('roots_only')
        if roots_only == 'true':
            return Category.objects.filter(parent__isnull=True)
        return super().get_queryset()

class AttributeDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AttributeDefinition.objects.all()
    serializer_class = AttributeDefinitionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        category_id = self.request.query_params.get('category')
        if category_id:
            return AttributeDefinition.objects.filter(category_id=category_id)
        return super().get_queryset()

class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [MarketplaceRateThrottle, VerifiedUserRateThrottle]

    def get_queryset(self):
        queryset = Listing.objects.all()
        
        # Search query
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(search_vector=search_query)

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Base filtering
        if self.request.user.is_authenticated:
            # Authors can see their own content, others only see active
            from django.db.models import Q
            queryset = queryset.filter(Q(status='active') | Q(user=self.request.user))
        else:
            queryset = queryset.filter(status='active')

        # Attribute filtering: ?attr_1=M&attr_5=Blue
        for param, value in self.request.query_params.items():
            if param.startswith('attr_'):
                try:
                    attr_split = param.split('_')
                    if len(attr_split) > 1:
                        attr_id = attr_split[1]
                        queryset = queryset.filter(
                            attribute_values__attribute_id=attr_id,
                            attribute_values__value=value
                        )
                except (IndexError, ValueError):
                    continue

        # Order by active promotions (Featured first, then Urgent)
        now = timezone.now()
        from django.db.models import Exists, OuterRef
        
        featured_exists = ListingPromotion.objects.filter(
            listing=OuterRef('pk'),
            promotion_type='featured',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        
        urgent_exists = ListingPromotion.objects.filter(
            listing=OuterRef('pk'),
            promotion_type='urgent',
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )

        queryset = queryset.annotate(
            is_featured=Exists(featured_exists),
            is_urgent=Exists(urgent_exists)
        ).order_by('-is_featured', '-is_urgent', '-created_at')
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Track view
        user = request.user if request.user.is_authenticated else None
        ListingView.objects.create(listing=instance, user=user)
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def renew(self, request, pk=None):
        listing = self.get_object()
        if listing.user != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Extend by 30 days and reset to active if expired
        listing.expires_at = timezone.now() + timezone.timedelta(days=30)
        if listing.status == 'expired':
            listing.status = 'active'
        listing.save()
        
        return Response({'status': 'renewed', 'expires_at': listing.expires_at})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def contact_seller(self, request, pk=None):
        listing = self.get_object()
        seller = listing.user
        buyer = request.user

        if seller == buyer:
            return Response({'error': 'You cannot contact yourself'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if either user has blocked the other
        if Block.objects.filter(user=buyer, blocked_user=seller).exists():
            return Response({'error': 'You have blocked this seller.'}, status=status.HTTP_403_FORBIDDEN)
        if Block.objects.filter(user=seller, blocked_user=buyer).exists():
            return Response({'error': 'This seller has blocked you.'}, status=status.HTTP_403_FORBIDDEN)

        # Find or create conversation
        conversation = Conversation.objects.filter(participants=buyer).filter(participants=seller).first()
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(buyer, seller)

        # Create pre-filled message
        message_text = f"Hi {seller.username}, I'm interested in your listing: {listing.title}.\nLink: http://localhost:3000/listings/{listing.id}/"
        
        Message.objects.create(
            conversation=conversation,
            sender=buyer,
            text=message_text
        )

        # Track contact click
        listing.contact_clicks += 1
        listing.save()

        return Response({
            'status': 'conversation started',
            'conversation_id': conversation.id
        }, status=status.HTTP_201_CREATED)

class ListingPromotionViewSet(viewsets.ModelViewSet):
    serializer_class = ListingPromotionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ListingPromotion.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # In a real app, you would integrate a payment gateway here.
        # For now, we simulate a successful transaction.
        serializer.save(
            user=self.request.user,
            is_active=True,
            transaction_id=f"TRANS_{random.getrandbits(32)}"
        )

class SavedSearchViewSet(viewsets.ModelViewSet):
    serializer_class = SavedSearchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.conversations.all().order_by('-updated_at')

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
        # If it's a group, the creator is an admin
        if conversation.type == 'group':
            conversation.admins.add(self.request.user)

    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        conversation = self.get_object()
        if conversation.type != 'group':
            return Response({'error': 'Participants can only be added to group conversations.'}, status=400)
        
        if not conversation.admins.filter(id=request.user.id).exists():
            return Response({'error': 'Only admins can add participants.'}, status=403)
            
        user_ids = request.data.get('user_ids', [])
        users = CustomUser.objects.filter(id__in=user_ids)
        conversation.participants.add(*users)
        return Response({'status': 'participants added'})

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        conversation = self.get_object()
        if conversation.type != 'group':
            return Response({'error': 'Participants can only be removed from group conversations.'}, status=400)
        
        if not conversation.admins.filter(id=request.user.id).exists():
            return Response({'error': 'Only admins can remove participants.'}, status=403)
            
        user_id = request.data.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            if conversation.admins.filter(id=user.id).exists() and conversation.admins.count() == 1:
                 return Response({'error': 'Cannot remove the last admin.'}, status=400)
            conversation.participants.remove(user)
            conversation.admins.remove(user)
            return Response({'status': 'participant removed'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            qs = Message.objects.filter(
                conversation_id=conversation_id,
                conversation__participants=self.request.user
            )
            # Filter out soft-deleted messages for the current user
            user = self.request.user
            qs = qs.exclude(sender=user, deleted_for_sender=True)
            qs = qs.exclude(~models.Q(sender=user), deleted_for_receiver=True)
            return qs
        return Message.objects.none()

    def perform_create(self, serializer):
        conversation = serializer.validated_data['conversation']
        sender = self.request.user
        
        if not conversation.participants.filter(id=sender.id).exists():
            raise permissions.PermissionDenied("You are not a participant in this conversation.")
            
        participants = conversation.participants.all()
        
        # Check if any other participant has blocked the sender or vice versa
        for participant in participants:
            if participant != sender:
                if Block.objects.filter(user=sender, blocked_user=participant).exists():
                    raise permissions.PermissionDenied("You have blocked a participant in this conversation.")
                if Block.objects.filter(user=participant, blocked_user=sender).exists():
                    raise permissions.PermissionDenied("A participant in this conversation has blocked you.")
        
        serializer.save(sender=sender)

    @action(detail=True, methods=['post'])
    def delete_for_me(self, request, pk=None):
        message = self.get_object()
        if message.sender == request.user:
            message.deleted_for_sender = True
        else:
            message.deleted_for_receiver = True
        message.save()
        return Response({'status': 'message hidden for user'})

class MessageSearchView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q')
        if not query:
            return Message.objects.none()
        
        user = self.request.user
        qs = Message.objects.filter(conversation__participants=user)
        
        # Hide soft-deleted messages
        qs = qs.exclude(sender=user, deleted_for_sender=True)
        qs = qs.exclude(~models.Q(sender=user), deleted_for_receiver=True)

        return qs.filter(text__icontains=query)

class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users see offers they received or sent
        return Offer.objects.filter(
            models.Q(listing__user=self.request.user) | 
            models.Q(buyer=self.request.user)
        )

    def perform_create(self, serializer):
        listing = serializer.validated_data['listing']
        if listing.user == self.request.user:
            raise serializers.ValidationError("You cannot make an offer on your own listing.")
        serializer.save(buyer=self.request.user)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        offer = self.get_object()
        if offer.listing.user != request.user:
            return Response({'error': 'Only the seller can accept offers'}, status=status.HTTP_403_FORBIDDEN)
        
        offer.status = 'accepted'
        offer.save()
        
        # Mark listing as sold? Depending on business logic. 
        # For now, just mark the offer.
        return Response({'status': 'offer accepted'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        offer = self.get_object()
        if offer.listing.user != request.user:
            return Response({'error': 'Only the seller can reject offers'}, status=status.HTTP_403_FORBIDDEN)
        
        offer.status = 'rejected'
        offer.save()
        return Response({'status': 'offer rejected'})

    @action(detail=True, methods=['post'])
    def counter(self, request, pk=None):
        offer = self.get_object()
        if offer.listing.user != request.user:
            return Response({'error': 'Only the seller can counter offers'}, status=status.HTTP_403_FORBIDDEN)
        
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        offer.status = 'countered'
        offer.countered_amount = amount
        offer.save()
        return Response({'status': 'counter-offer sent', 'amount': amount})

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only staff can update report status")
        serializer.save()

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users see orders they bought or sold
        return Order.objects.filter(
            models.Q(buyer=self.request.user) | 
            models.Q(seller=self.request.user)
        )

    def perform_create(self, serializer):
        listing = serializer.validated_data['listing']
        delivery_option = serializer.validated_data['delivery_option']
        
        # Validate delivery option
        if delivery_option == 'shipping' and not listing.shipping_available:
            raise serializers.ValidationError("Shipping is not available for this listing.")
        if delivery_option == 'pickup' and not listing.local_pickup:
            raise serializers.ValidationError("Local pickup is not available for this listing.")
            
        amount = listing.price or 0
        if delivery_option == 'shipping' and listing.shipping_cost:
            amount += listing.shipping_cost
            
        # Platform fee (e.g. 5%)
        platform_fee = amount * Decimal('0.05')
        
        serializer.save(
            buyer=self.request.user,
            seller=listing.user,
            amount=amount,
            platform_fee=platform_fee
        )

    @action(detail=True, methods=['post'])
    def confirm_receipt(self, request, pk=None):
        order = self.get_object()
        if order.buyer != request.user:
            return Response({'error': 'Only the buyer can confirm receipt.'}, status=403)
        
        if order.status != 'shipped':
            return Response({'error': 'Order must be in shipped status.'}, status=400)
            
        order.status = 'completed'
        order.confirmed_at = timezone.now()
        order.payout_released = True
        order.save()
        return Response({'status': 'order completed, payment released to seller'})

class DisputeViewSet(viewsets.ModelViewSet):
    serializer_class = DisputeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Dispute.objects.all()
        # Users see disputes related to their orders
        return Dispute.objects.filter(
            models.Q(order__buyer=self.request.user) | 
            models.Q(order__seller=self.request.user)
        )

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        # Check if user is part of the order
        if order.buyer != self.request.user and order.seller != self.request.user:
            raise permissions.PermissionDenied("You are not part of this order")
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            # Users can't update status, only other fields if allowed (metadata?)
            # For simplicity, only staff can update disputes for now
            raise permissions.PermissionDenied("Only staff can update dispute details")
        serializer.save()

class DisputeMessageViewSet(viewsets.ModelViewSet):
    serializer_class = DisputeMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        dispute_id = self.request.query_params.get('dispute')
        if dispute_id:
            return DisputeMessage.objects.filter(
                dispute_id=dispute_id,
                dispute__order__buyer=self.request.user
            ) | DisputeMessage.objects.filter(
                dispute_id=dispute_id,
                dispute__order__seller=self.request.user
            ) | DisputeMessage.objects.filter(
                dispute_id=dispute_id,
                dispute__created_by=self.request.user
            )
        return DisputeMessage.objects.none()

    def perform_create(self, serializer):
        dispute = serializer.validated_data['dispute']
        # Check if user is part of the dispute
        if (dispute.order.buyer != self.request.user and 
            dispute.order.seller != self.request.user and 
            not self.request.user.is_staff):
            raise permissions.PermissionDenied("You are not part of this dispute")
        serializer.save(sender=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users see reviews they wrote or received
        return Review.objects.filter(
            models.Q(reviewer=self.request.user) | 
            models.Q(reviewee=self.request.user)
        )

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        
        # Only buyer can review
        if order.buyer != self.request.user:
            raise permissions.PermissionDenied("Only the buyer can review the order")
            
        # Check if already reviewed (unique constraint handled by OneToOneField, but nice to catch)
        if hasattr(order, 'review'):
            raise serializers.ValidationError("This order has already been reviewed")
            
        serializer.save(
            reviewer=self.request.user,
            reviewee=order.seller
        )

class WishlistItemViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SellerFollowViewSet(viewsets.ModelViewSet):
    serializer_class = SellerFollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def seller_stats(self, request):
        user = request.user
        listings = Listing.objects.filter(user=user)
        
        total_views = ListingView.objects.filter(listing__user=user).count()
        total_clicks = sum(l.contact_clicks for l in listings)
        
        orders = Order.objects.filter(seller=user)
        total_sales = orders.count()
        
        conversion_rate = (total_sales / total_views * 100) if total_views > 0 else 0
        
        # Monthly Revenue Chart
        from django.db.models.functions import TruncMonth
        from django.db.models import Sum
        
        revenue_data = Order.objects.filter(seller=user, status='completed') \
            .annotate(month=TruncMonth('created_at')) \
            .values('month') \
            .annotate(revenue=Sum('amount')) \
            .order_by('month')

        return Response({
            'total_views': total_views,
            'contact_clicks': total_clicks,
            'total_sales': total_sales,
            'conversion_rate': round(conversion_rate, 2),
            'revenue_chart': revenue_data
        })

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Mock stripe subscription creation
        serializer.save(user=self.request.user, status='active')

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def buy_currency(self, request, pk=None):
        wallet = self.get_object()
        amount = request.data.get('amount')
        if not amount or Decimal(str(amount)) <= 0:
            return Response({'error': 'Invalid amount'}, status=400)
        
        # mock stripe payment
        import uuid
        VirtualTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='credit',
            description='Buy currency via Stripe',
            reference=f'ch_{uuid.uuid4().hex[:12]}'
        )
        wallet.balance += Decimal(str(amount))
        wallet.save()
        return Response({'status': 'currency purchased', 'balance': str(wallet.balance)})

class PayoutViewSet(viewsets.ModelViewSet):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # In real app, check if user has enough balance/completed orders
        serializer.save(user=self.request.user, status='requested')

class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from django.db.models import Q
        return Referral.objects.filter(Q(referrer=self.request.user) | Q(referred_user=self.request.user))
