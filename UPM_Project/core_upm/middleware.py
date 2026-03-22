from django.utils import timezone


class OnlineStatusMiddleware:
    """Updates last_seen and is_online for every authenticated request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                now = timezone.now()
                profile.last_seen = now
                profile.is_online = True
                profile.save(update_fields=['last_seen', 'is_online'])
            except Exception:
                pass

        return response
