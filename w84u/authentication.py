from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.authentication import JWTAuthentication


# кастомный класс для аутентификации jwt из куков
class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        cookie_token = request.COOKIES.get('access_token')

        if not cookie_token:
            return None  # Если токен отсутствует, возвращаем None

        try:
            validated_token = JWTAuthentication().get_validated_token(cookie_token)

        except AuthenticationFailed:
            raise AuthenticationFailed('Invalid token')

        user = JWTAuthentication().get_user(validated_token)

        if user.is_anonymous:  # Проверяем, что пользователь не анонимный
            raise AuthenticationFailed('User is anonymous')

        return (user, validated_token)  # Возвращаем кортеж (пользователь, токен)

