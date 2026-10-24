from django.utils import timezone
from django.core.cache import cache


class OnlineStatusMiddleware:
    """
    Updates last_seen for JWT-authenticated requests.
    Uses simplejwt to decode the Authorization header directly,
    since DRF authentication runs inside the view, not in middleware.
    Throttled to one DB write per user per 60 seconds via cache.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return response

        token_str = auth_header.split(' ', 1)[1]
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth.models import User

            token = AccessToken(token_str)
            user_id = token.get('user_id')
            if not user_id:
                return response

            # Throttle: only update DB once per 60s per user
            cache_key = f'online_status_{user_id}'
            if cache.get(cache_key):
                return response

            user = User.objects.select_related('profile').get(id=user_id)
            now = timezone.now()
            user.profile.last_seen = now
            user.profile.is_online = True
            user.profile.save(update_fields=['last_seen', 'is_online'])
            cache.set(cache_key, True, timeout=60)
        except Exception:
            pass

        return response
