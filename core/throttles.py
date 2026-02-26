from rest_framework.throttling import UserRateThrottle

class AuthRateThrottle(UserRateThrottle):
    scope = 'auth'

class PostRateThrottle(UserRateThrottle):
    scope = 'posts'

class MarketplaceRateThrottle(UserRateThrottle):
    scope = 'marketplace'

class VerifiedUserRateThrottle(UserRateThrottle):
    scope = 'verified_user'

    def allow_request(self, request, view):
        # Only apply if user is verified
        if request.user.is_authenticated and request.user.is_verified:
            return super().allow_request(request, view)
        return True # Fall back to other throttles
