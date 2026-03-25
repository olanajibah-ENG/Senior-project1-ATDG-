class AllowAllHostsMiddleware:
    """
    Patches the request to prevent DisallowedHost errors
    caused by Docker service names with underscores (e.g. ai_django_app:8000).
    Must be the FIRST middleware in the list.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Override get_host to never raise DisallowedHost
        request.get_host = lambda: request.META.get('HTTP_HOST', 'localhost')
        return self.get_response(request)
