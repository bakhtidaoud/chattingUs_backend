"""
Serializers for the users app.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, Follow, Block
from .utils import send_verification_email, send_welcome_email


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'phone_number']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Send verification email
        try:
            send_verification_email(user, self.context.get('request'))
        except Exception as e:
            print(f"Failed to send verification email: {e}")
        
        # Send welcome email
        try:
            send_welcome_email(user)
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with email, username, or phone.
    """
    identifier = serializers.CharField(required=True, help_text="Email, username, or phone number")
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        identifier = attrs.get('identifier')
        password = attrs.get('password')
        
        # Try to find user by email, username, or phone
        user = None
        if '@' in identifier:
            # Email login
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                pass
        elif identifier.isdigit():
            # Phone login
            try:
                user = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                pass
        else:
            # Username login
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                pass
        
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")
        
        # Authenticate user
        user = authenticate(username=user.username, password=password)
        
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'bio', 
                  'profile_picture', 'date_of_birth', 'phone_number', 'is_verified', 
                  'is_private', 'email_verified', 'phone_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_verified', 'email_verified', 'phone_verified', 
                           'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'followers_count', 'following_count', 'posts_count', 'is_private']


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(required=True)


class PhoneVerificationSerializer(serializers.Serializer):
    """
    Serializer for phone verification.
    """
    code = serializers.CharField(required=True, max_length=6, min_length=6)


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for Follow model.
    """
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'created_at']


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Serializer for public user profiles (limited information).
    """
    is_following = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'bio', 
                  'profile_picture', 'is_verified', 'is_private', 
                  'is_following', 'is_blocked', 'followers_count', 
                  'following_count', 'posts_count', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at']
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False
    
    def get_is_blocked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import Block
            return Block.objects.filter(blocker=request.user, blocked=obj).exists()
        return False
    
    def get_followers_count(self, obj):
        try:
            return obj.profile.followers_count
        except:
            return 0
    
    def get_following_count(self, obj):
        try:
            return obj.profile.following_count
        except:
            return 0
    
    def get_posts_count(self, obj):
        try:
            return obj.profile.posts_count
        except:
            return 0


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'date_of_birth', 
                  'phone_number', 'is_private']
    
    def validate_username(self, value):
        from .profile_utils import validate_username
        is_valid, message = validate_username(value)
        if not is_valid:
            raise serializers.ValidationError(message)
        
        # Check if username is already taken
        user = self.context['request'].user
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Username is already taken.")
        
        return value


class ProfilePictureSerializer(serializers.Serializer):
    """
    Serializer for profile picture upload.
    """
    picture = serializers.ImageField(required=True)
    
    def validate_picture(self, value):
        # Validate file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image file size cannot exceed 5MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only JPEG, PNG, and WebP images are allowed.")
        
        return value


class BlockSerializer(serializers.ModelSerializer):
    """
    Serializer for Block model.
    """
    blocker = UserSerializer(read_only=True)
    blocked = PublicUserSerializer(read_only=True)
    
    class Meta:
        model = Block
        fields = ['id', 'blocker', 'blocked', 'created_at']
        read_only_fields = ['id', 'created_at']
