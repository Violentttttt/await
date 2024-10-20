# middlewares.py

from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from asgiref.sync import sync_to_async


# хуйня
@sync_to_async
def get_user_from_jwt(token):
    try:
        # Попытка валидации JWT
        UntypedToken(token)
        validated_token = JWTAuthentication().get_validated_token(token)
        return JWTAuthentication().get_user(validated_token)
    except (InvalidToken, TokenError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        cookies = scope.get('headers', [])
        jwt_token = None

        # Поиск JWT токена в cookies
        for header in cookies:
            if header[0] == b'cookie':
                cookie_value = header[1].decode()
                for cookie in cookie_value.split(';'):
                    if cookie.strip().startswith('access_token'):
                        jwt_token = cookie.split('=')[1]
                        break

        # Если нашли токен, пытаемся аутентифицировать
        if jwt_token:
            scope['user'] = await get_user_from_jwt(jwt_token)
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
