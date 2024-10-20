import traceback
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets, status, generics
from .authentication import CookieJWTAuthentication
from .models import CustomUser, Marker, MarkerHistory, Match, Message, Session, OptionalInfo, MaybeMatch
from .serializers import CustomUserSerializer, MarkerSerializer, MarkerHistorySerializer, MatchSerializer, \
    MessageSerializer, SessionSerializer, OptionalInfoSerializer, MaybeMatchSerializer, HistorySerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from django.views import View
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from w84u.timeCompare import combine_date_time, create_datetime_range
from django.db.models import Q, F
from psycopg2.extras import DateTimeRange
from django.utils.dateparse import parse_datetime
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import GEOSGeometry
from geopy.distance import geodesic
from .services import handle_session_save


class RegisterAPIView(APIView):
    def post(self, request):

        print(request.data)
        username = request.data.get('username')
        email = request.data.get('email')
        real_name = request.data.get('real_name')
        gender = request.data.get("gender")
        age = request.data.get('age')
        password = request.data.get('password')

        # Checking if username or email already exists

        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Creating the user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                real_name=real_name,
                gender=gender,
                age=age
            )

            # Generating JWT tokens
            refresh = RefreshToken.for_user(user)

            # Creating a response with tokens and setting the access_token in cookies
            response = Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
            response.set_cookie(
                key='access_token',
                value=str(refresh.access_token),
                httponly=True,

            )
            print(response.set_cookie)
            return response
        except Exception as ex:
            print(f"Error during registration: {ex}")
            return Response({"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginAPIView(APIView):

    def post(self, request, *args, **kwargs):

        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=400)

        user = authenticate(username=user.email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            response = Response()

            response.set_cookie(
                key='access_token',
                value=str(refresh.access_token),
                httponly=True,  # Кука будет доступна только серверу
                samesite=None,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                samesite=None,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()
            )

            print(response.cookies)
            response.data = {"message": "Logged in successfully"}
            return response

        return Response({'error': 'Invalid credentials'}, status=400)

    def get(self, request):
        if request.user.is_authenticated:
            return Response({"message": "User is authenticated", "user": request.user.username},
                            status=status.HTTP_200_OK)
        else:
            return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):

    def post(self, request):
        response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/')

        return response


# Функция для генерации токена для ws
def get_user_token(user):
    token, created = Token.objects.get_or_create(user=user)

    if not created:

        if token.created < timezone.now() - timedelta(days=1):
            token.delete()
            token = Token.objects.create(user=user)

    return token.key


class Save_infoView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            user = request.user

            data = request.data.copy()
            data['user'] = user.id

            # Получаем маркеры
            red_marker_id = request.COOKIES.get('red_marker_id')
            blue_marker_id = request.COOKIES.get('blue_marker_id')

            red_marker = Marker.objects.filter(id=red_marker_id).first()
            blue_marker = Marker.objects.filter(id=blue_marker_id).first()

            print("Request data:", request.data)

            # Обработка дат и времени с использованием функций
            single_datetime = combine_date_time(request.data.get('date'), request.data.get('time'))
            datetime_range = create_datetime_range(
                request.data.get('startDate'),
                request.data.get('endDate'),
                request.data.get('startTime'),
                request.data.get('endTime')
            )

            print("Single datetime:", single_datetime)
            print("Datetime range:", datetime_range)

            # Создаем и проверяем сериализатор
            serializer = SessionSerializer(data=data)
            if serializer.is_valid():
                # Сохраняем объект в зависимости от того, что пришло — точная дата/время или диапазон
                if single_datetime:
                    post_new = serializer.save(
                        user=user,
                        red_marker=red_marker,
                        blue_marker=blue_marker,
                        name=data.get('name'),
                        gender=data.get('gender'),
                        date=single_datetime,
                        datetime_range=None,
                        surname=data.get('surname'),
                        more_info=data.get('more_info'),
                        image=request.FILES.get('photo'),
                        is_active=True,
                    )
                elif datetime_range:
                    post_new = Session.objects.create(
                        user=user,
                        red_marker=red_marker,
                        blue_marker=blue_marker,
                        name=data.get('name'),
                        gender=data.get('gender'),
                        date=None,
                        datetime_range=datetime_range,
                        surname=data.get('surname'),
                        more_info=data.get('more_info'),
                        image=request.FILES.get('photo'),
                        is_active=True,
                    )
                    # post_new = serializer.save(
                    #     user=user,
                    #     red_marker=red_marker,
                    #     blue_marker=blue_marker,
                    #     name=data.get('name'),
                    #     gender=data.get('gender'),
                    #     date=None,
                    #     datetime_range=datetime_range,
                    #     surname=data.get('surname'),
                    #     more_info=data.get('more_info'),
                    #     image=request.FILES.get('photo')
                    # )

                else:
                    return Response({"error": "Neither single datetime nor range provided"},
                                    status=status.HTTP_400_BAD_REQUEST)
                # handle_session_save(Session, post_new, created=True) у меня post_save стоит
                return Response({'post': SessionSerializer(post_new).data}, status=status.HTTP_201_CREATED)
            else:
                print("Serializer errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            traceback.print_exc()
            print("Error occurred:", str(e))
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SaveLocationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data
            red_location = data.get('myLocation')
            blue_location = data.get('targetLocation')

            user = request.user
            if not user.is_authenticated:
                return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

            response = Response()

            if red_location and blue_location:
                red_marker_data = {
                    'user': user.id,
                    'latitude': red_location['lat'],
                    'longitude': red_location['lng'],
                    'type': 'red',
                    'created_at': datetime.now()
                }
                blue_marker_data = {
                    'user': user.id,
                    'latitude': blue_location['lat'],
                    'longitude': blue_location['lng'],
                    'type': 'blue',
                    'created_at': datetime.now()
                }
                red_marker_serializer = MarkerSerializer(data=red_marker_data)
                blue_marker_serializer = MarkerSerializer(data=blue_marker_data)

                if red_marker_serializer.is_valid() and blue_marker_serializer.is_valid():
                    red_marker = red_marker_serializer.save()
                    blue_marker = blue_marker_serializer.save()
                    print('данные сохранились')
                    response.set_cookie(
                        key='blue_marker_id',
                        value=str(blue_marker.id),
                        httponly=True,

                    )
                    response.set_cookie(
                        key='red_marker_id',
                        value=str(red_marker.id),
                        httponly=True,
                    )
                    print('куки установлены')
                    return response

            return Response({"status": "success", "msg": "Coordinates saved"})
        except Exception as e:
            return Response({"status": "error", "msg": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountView(APIView):  # класс загрузки данных из таблицы CustomUser
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            response = Response()
            if request.COOKIES.get('blue_marker_id'):
                response.delete_cookie('blue_marker_id', path='/')

            if request.COOKIES.get('red_marker_id'):
                response.delete_cookie('red_marker_id', path='/')
            info = request.user

        except CustomUser.DoesNotExist:
            return Response({"detail": "Информация не найдена"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomUserSerializer(info)
        response.data = serializer.data
        return response


class OptionalInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            optional_info = OptionalInfo.objects.get(user=request.user)
        except OptionalInfo.DoesNotExist:
            # Создаем запись, если не найдена
            optional_info = OptionalInfo.objects.create(user=request.user)

        serializer = OptionalInfoSerializer(optional_info)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        try:
            optional_info = OptionalInfo.objects.get(user=request.user)
        except OptionalInfo.DoesNotExist:
            return Response({"error": "OptionalInfo not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OptionalInfoSerializer(optional_info, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MaybeMatchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = MaybeMatch.objects.filter(
            (Q(id_confirmed_by_user1=False) & Q(user_1=request.user)) |
            (Q(id_confirmed_by_user2=False) & Q(user_2=request.user))
        )

        count = params.count()

        if count > 0:
            matches_data = []
            seen = set()  # Для отслеживания уникальных записей
            to_delete = []  # Список для хранения записей, которые нужно удалить

            for match in params:
                # Определяем уникальный идентификатор для пары
                match_id = (match.user_1.id, match.user_2.id)

                if match_id in seen:
                    to_delete.append(match)  # Добавляем запись в список для удаления
                    continue
                else:
                    seen.add(match_id)

                    # Определяем, какие данные показывать
                    if match.user_2 == request.user:
                        search_name = match.session_2
                        is_it_him = match.user_1
                        his_picture = match.user_1.optionalinfo
                        about_him = match.user_1.optionalinfo
                    else:
                        search_name = match.session_1
                        is_it_him = match.user_2
                        his_picture = match.user_2.optionalinfo
                        about_him = match.user_2.optionalinfo

                    match_info = {
                        'maybematch': MaybeMatchSerializer(match).data,
                        'search_name': SessionSerializer(search_name).data,
                        'is_it_him': CustomUserSerializer(is_it_him).data,
                        'his_picture': OptionalInfoSerializer(his_picture).data,
                        'about_him': OptionalInfoSerializer(about_him).data,
                    }

                    matches_data.append(match_info)

            # Удаляем дубли после завершения обработки всех записей
            for match in to_delete:
                match.delete()

            data = {
                'count': count,  # Количество найденных матчей
                'matches': matches_data,  # Сами матчи
            }

        else:
            data = {
                'count': 0,
                'matches': []
            }

        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            match_id = request.data.get('matchId')
            action = request.data.get('action')
            match = MaybeMatch.objects.get(id=match_id)

            if action == 'True':
                if request.user == match.user_1:
                    MaybeMatch.objects.filter(user_1=match.user_1, user_2=match.user_2).update(
                        id_confirmed_by_user1=True
                    )
                elif request.user == match.user_2:
                    MaybeMatch.objects.filter(user_1=match.user_1, user_2=match.user_2).update(
                        id_confirmed_by_user2=True
                    )
            else:
                MaybeMatch.objects.filter(user_1=match.user_1, user_2=match.user_2).delete()

            return Response(status=status.HTTP_201_CREATED)

        except MaybeMatch.DoesNotExist:
            return Response({"error": "Match not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("Error occurred:", str(e))
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MatchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        maybematches = MaybeMatch.objects.filter(
            (Q(user_1=request.user) | Q(user_2=request.user)) &
            Q(id_confirmed_by_user1=True) &
            Q(id_confirmed_by_user2=True)
        )

        if maybematches.exists():
            for i in maybematches:
                # Проверяем, существует ли уже такой матч
                match_exists = Match.objects.filter(
                    user_1=i.user_1,
                    session_1=i.session_1,
                    user_2=i.user_2,
                    session_2=i.session_2
                ).exists()

                if not match_exists:
                    Match.objects.create(
                        user_1=i.user_1,
                        session_1=i.session_1,
                        user_2=i.user_2,
                        session_2=i.session_2,
                    )

                    i.session_1.is_active = False
                    i.session_1.save()
                    i.session_2.is_active = False
                    i.session_2.save()

            matches = Match.objects.filter(
                Q(user_1=request.user) | Q(user_2=request.user)
            )
            serializer = MatchSerializer(matches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response({'detail': 'No matches found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ses = Session.objects.filter(user=request.user, is_active=True)
        serializer = HistorySerializer(ses, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class WSAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        acs = request.COOKIES.get('access_token')
        ws_token = get_user_token(request.user)
        response = Response()
        response.data = ws_token
        return response


"""API к бд"""


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    # permission_classes = [IsAdminUser, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['email']


class OptionalInfoViewSet(viewsets.ModelViewSet):
    queryset = OptionalInfo.objects.all()
    serializer_class = OptionalInfoSerializer
    # permission_classes = [IsAdminUser, ]


class MarkerViewSet(viewsets.ModelViewSet):
    queryset = Marker.objects.all()
    serializer_class = MarkerSerializer
    # permission_classes = [IsAdminUser, ]


class MarkerHistoryViewSet(viewsets.ModelViewSet):
    queryset = MarkerHistory.objects.all()
    serializer_class = MarkerHistorySerializer
    # permission_classes = [IsAdminUser, ]


class MaybeMatchViewSet(viewsets.ModelViewSet):
    queryset = MaybeMatch.objects.all()
    serializer_class = MaybeMatchSerializer


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer


#     # permission_classes = [IsAdminUser, ]


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    # permission_classes = [IsAdminUser, ]


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer


#     permission_classes = [IsAdminUser, ]


# class TokenVerifyView(APIView):
#     authentication_classes = [CookieJWTAuthentication]
#
#     def post(self, request):
#         return Response({"detail": "Token is valid."}, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenViewBase):

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({"detail": "Refresh token not found in cookies."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Создаем новый access токен
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

            response = Response({"access": new_access_token}, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=new_access_token,
                httponly=True,
                secure=False,  # Установите True для HTTPS
                samesite='None',
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
            )
            return response

        except InvalidToken:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)


class Verify_for_app(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        # print(request.COOKIES)
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return Response({"detail": "Access token is missing."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            jwt_authenticator = JWTAuthentication()
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

            # Попытка аутентификации пользователя
            user, _ = jwt_authenticator.authenticate(request)

            if user is None:
                raise AuthenticationFailed("User not authenticated.")

            # Если аутентификация успешна, возвращаем ответ с данными пользователя
            return Response({"detail": "Authenticated", "user": user.email}, status=status.HTTP_200_OK)

        except AuthenticationFailed as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({"detail": "An error occurred."}, status=status.HTTP_400_BAD_REQUEST)
