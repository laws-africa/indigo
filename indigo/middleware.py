from django.http import HttpResponsePermanentRedirect


class GazettesRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_raw_uri() == "https://edit.laws.africa/next-task":
            return HttpResponsePermanentRedirect("https://gazettes.laws.africa/next-task")
        return self.get_response(request)
