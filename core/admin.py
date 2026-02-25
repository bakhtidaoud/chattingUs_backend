from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Post, PostMedia, SMSDevice, Like, Comment, Hashtag, Follow, Notification, Block, Mute, FeedPost, Story, StoryView, StoryReaction, Highlight, HighlightItem, Category, Listing, AttributeDefinition, AttributeOption, ListingAttributeValue

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

class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingAttributeValueInline]
    list_display = ['title', 'user', 'category', 'price', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'description', 'user__username']

admin.site.register(Listing, ListingAdmin)
