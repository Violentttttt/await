import math
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from w84u.forms import UserRegistrationForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
import json
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status, generics
from .models import CustomUser, Marker, MarkerHistory, Match, Message, Session, OptionalInfo, MaybeMatch
from .serializers import CustomUserSerializer, MarkerSerializer, MarkerHistorySerializer, MatchSerializer, \
    MessageSerializer, SessionSerializer, OptionalInfoSerializer, MaybeMatchSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
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


# Create your views here.
def main(request):
    context = {}

    return render(request, 'w84u/main.html', context)


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.username = new_user.email
            new_user.save()
            return redirect('/login/')
    else:
        user_form = UserRegistrationForm()
    return render(request, 'w84u/register.html', {'user_form': user_form})


def get_user_token(user):
    token, created = Token.objects.get_or_create(user=user)
    return token.key


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = CustomUser.objects.filter(email=email).first()
            if user:
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        print("User authenticated and logged in successfully")
                        token = get_user_token(user)
                        response = redirect(f'http://localhost:3000/account?token={token}')
                        print(response.status_code)  # Должно быть 302
                        return response
                    else:
                        print("User account is disabled")
                        return render(request, 'w84u/login.html',
                                      {'form': form, 'error_message': 'Your account is disabled.'})
                else:
                    print("Invalid login attempt")
                    return render(request, 'w84u/login.html', {'form': form, 'error_message': 'Invalid login attempt.'})
            else:
                print("User not found")
                return render(request, 'w84u/login.html', {'form': form, 'error_message': 'Invalid login attempt.'})
        else:
            print("Form is not valid")
    else:
        form = LoginForm()
    return render(request, 'w84u/login.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('/')


def map_view(request):
    return render(request, 'w84u/W4U.html', {})


class Save_infoView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            # Извлечение токена из заголовка запроса
            auth_header = request.headers.get('Authorization')
            if auth_header:
                token_key = auth_header.split(' ')[1]  # Предполагаем формат 'Token <token>'
                try:
                    token = Token.objects.get(key=token_key)
                    user = token.user
                except Token.DoesNotExist:
                    return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({"error": "Token not provided"}, status=status.HTTP_401_UNAUTHORIZED)

            # Копируем данные запроса в изменяемый словарь
            data = request.data.copy()
            data['user'] = user.id

            # Получаем маркеры
            red_marker_id = request.data.get('savedRedMarkerId')
            blue_marker_id = request.data.get('savedBlueMarkerId')
            red_marker = Marker.objects.filter(id=red_marker_id).first()
            blue_marker = Marker.objects.filter(id=blue_marker_id).first()
            if red_marker_id and not red_marker:
                return Response({"error": "Red marker not found"}, status=status.HTTP_400_BAD_REQUEST)
            if blue_marker_id and not blue_marker:
                return Response({"error": "Blue marker not found"}, status=status.HTTP_400_BAD_REQUEST)

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
                        image=request.FILES.get('photo')
                    )
                elif datetime_range:
                    post_new = serializer.save(
                        user=user,
                        red_marker=red_marker,
                        blue_marker=blue_marker,
                        name=data.get('name'),
                        gender=data.get('gender'),
                        date=None,
                        datetime_range=datetime_range,
                        surname=data.get('surname'),
                        more_info=data.get('more_info'),
                        image=request.FILES.get('photo')
                    )
                else:
                    return Response({"error": "Neither single datetime nor range provided"},
                                    status=status.HTTP_400_BAD_REQUEST)
                # handle_session_save(Session, post_new, created=True) у меня post_save стоит
                return Response({'post': SessionSerializer(post_new).data}, status=status.HTTP_201_CREATED)
            else:
                print("Serializer errors:", serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("Error occurred:", str(e))
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SaveLocationsView(APIView):
    def post(self, request):
        try:
            data = request.data
            red_location = data.get('myLocation')
            blue_location = data.get('targetLocation')

            user = request.user
            if not user.is_authenticated:
                return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

            response_data = {}

            if red_location:
                red_marker_data = {
                    'user': user.id,
                    'latitude': red_location['lat'],
                    'longitude': red_location['lng'],
                    'type': 'red',
                    'created_at': datetime.now()
                }
                red_marker_serializer = MarkerSerializer(data=red_marker_data)
                if red_marker_serializer.is_valid():
                    red_marker = red_marker_serializer.save()
                    response_data['red_marker_id'] = red_marker.id
                else:
                    return Response(red_marker_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if blue_location:
                blue_marker_data = {
                    'user': user.id,
                    'latitude': blue_location['lat'],
                    'longitude': blue_location['lng'],
                    'type': 'blue',
                    'created_at': datetime.now()
                }
                blue_marker_serializer = MarkerSerializer(data=blue_marker_data)
                if blue_marker_serializer.is_valid():
                    blue_marker = blue_marker_serializer.save()
                    response_data['blue_marker_id'] = blue_marker.id
                else:
                    return Response(blue_marker_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({"status": "success", "msg": "Coordinates saved", "data": response_data},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "msg": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorldView(APIView): #мусор ебаный

    def get(self, request):
        # Здесь можете добавить логику получения данных, которые будут возвращены
        data = {
            "message": "Hello from Django"
        }
        return Response(data, status=status.HTTP_200_OK)


class AccountView(APIView):  # класс загрузки данных из таблицы CustomUser
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            info = request.user
        except CustomUser.DoesNotExist:
            return Response({"detail": "Информация не найдена"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomUserSerializer(info)
        return Response(serializer.data, status=status.HTTP_200_OK)


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




class TimeCompare(View):
    def get(self, request, pk):
        try:
            # Получаем последнюю сессию пользователя
            exclude_session = Session.objects.filter(user=pk).latest('created_at')
            print(exclude_session.date)
            print(exclude_session.datetime_range)

        except Session.DoesNotExist:
            return HttpResponse('Сессия не найдена', status=404)

        filtered = Session.objects.none()

        if exclude_session.date != None:
            filtered = Session.objects.filter(
                Q(datetime_range__contains=exclude_session.date) | Q(date=exclude_session.date))
        elif exclude_session.datetime_range != None:
            filtered = Session.objects.filter(Q(datetime_range__overlap=exclude_session.datetime_range) | Q(
                datetime_range=exclude_session.datetime_range))

        filtered_sessions = filtered.filter(
            # is_active=True
        ).exclude(pk=exclude_session.pk)
        print(filtered_sessions)

        return HttpResponse(f'Отфильтрованные по времени сессии: {filtered_sessions}')


class GeoCompare(View):
    def get(self, request, pk):
        try:
            exclude_session = Session.objects.filter(user=pk).latest('created_at')

            blue_marker = exclude_session.blue_marker
            red_marker = exclude_session.red_marker

        except Session.DoesNotExist:
            return HttpResponse('Сессия не найдена', status=404)

        if blue_marker and red_marker:
            radius_km = 0.05  # 50 метров

            blue_point = GEOSGeometry(blue_marker.location)
            red_point = GEOSGeometry(red_marker.location)

            print("Blue point:", blue_point)
            print("Red point:", red_point)

            filtered_sessions = Session.objects.annotate(
                distance_blue=Distance('blue_marker__location', red_point),
                distance_red=Distance('red_marker__location', blue_point)
            ).filter(
                distance_blue__lte=D(km=radius_km),
                distance_red__lte=D(km=radius_km)
            ).exclude(pk=exclude_session.pk)

            print("Filtered sessions:", filtered_sessions)
            session_ids = [session.pk for session in filtered_sessions]
            return HttpResponse(f'Результаты фильтрации: {session_ids}')
        else:
            return HttpResponse('Не найдено достаточного количества маркеров', status=404)


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
                'count': len(matches_data),
                'matches': matches_data,
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
            return Response({'detail': 'No matches found'}, status=status.HTTP_404_NOT_FOUND)

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
