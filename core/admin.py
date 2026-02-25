from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, Post, PostMedia, SMSDevice, Like, Comment

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
