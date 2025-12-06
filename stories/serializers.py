from rest_framework import serializers
from .models import Story, StoryView, StoryHighlight, StoryReply
from users.serializers import UserSerializer

class StorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_viewed = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ['id', 'user', 'media', 'media_type', 'text', 'duration', 'views_count', 'created_at', 'expires_at', 'is_viewed']
        read_only_fields = ['views_count', 'expires_at']

    def get_is_viewed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return StoryView.objects.filter(story=obj, user=user).exists()
        return False

class StoryViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryView
        fields = '__all__'

class StoryHighlightSerializer(serializers.ModelSerializer):
    stories = StorySerializer(many=True, read_only=True)
    story_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Story.objects.all(), source='stories'
    )

    class Meta:
        model = StoryHighlight
        fields = ['id', 'user', 'title', 'cover', 'stories', 'story_ids', 'created_at']
        read_only_fields = ['user']

class StoryReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StoryReply
        fields = ['id', 'story', 'user', 'text', 'created_at']
        read_only_fields = ['user']
