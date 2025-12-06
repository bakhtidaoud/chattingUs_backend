from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoryViewSet, StoryHighlightViewSet, StoryReplyViewSet

router = DefaultRouter()
router.register(r'highlights', StoryHighlightViewSet, basename='highlight')
router.register(r'replies', StoryReplyViewSet, basename='reply')
router.register(r'', StoryViewSet, basename='story')

urlpatterns = [
    path('', include(router.urls)),
]
