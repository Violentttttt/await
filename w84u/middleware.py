# middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse

class ClearCookiesOnLogoutMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code == 401:  # Если токен недействителен или истек
            response.delete_cookie('access_token')
        return response
