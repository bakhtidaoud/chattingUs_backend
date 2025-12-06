from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExploreViewSet, HashtagViewSet

router = DefaultRouter()
router.register(r'hashtags', HashtagViewSet, basename='hashtag')
router.register(r'', ExploreViewSet, basename='explore')

urlpatterns = [
    path('', include(router.urls)),
]
