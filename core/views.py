from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
import random
from django.utils import timezone
from .models import CustomUser, UserEmailVerification, SMSDevice, Post, PostMedia, Like, Comment, Hashtag, Follow, Notification, Block, Mute, FeedPost, SavedCollection, SavedItem, Story, StoryView
from .utils import send_verification_email, send_sms
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer, 
    CustomTokenObtainSlidingSerializer, PasswordChangeSerializer,
    PostSerializer, PostMediaSerializer, LikeSerializer, CommentSerializer,
    HashtagSerializer, FollowSerializer, NotificationSerializer,
    BlockSerializer, MuteSerializer,
    SavedCollectionSerializer, SavedItemSerializer,
    StorySerializer, StoryViewSerializer
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

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.all().order_by('-created_at')
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
        serializer.save(user=self.request.user)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
            Notification.objects.create(
                recipient=target_user,
                sender=request.user,
                notification_type='follow_request'
            )
            return Response({'status': 'requested'}, status=status.HTTP_201_CREATED)
        else:
            Notification.objects.create(
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
        my_following = Follow.objects.filter(follower=user).values_list('followed_id', flat=True)
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

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked as read'})

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
