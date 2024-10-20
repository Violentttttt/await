import asyncio
from datetime import datetime
from random import randint
from time import sleep
import json
from asgiref.sync import sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from rest_framework import status

from w84u.geo_save import save_location
from w84u.middlewares import get_user_from_jwt

from channels.db import database_sync_to_async
from .models import MaybeMatch, Match
from .serializers import MaybeMatchSerializer, SessionSerializer, CustomUserSerializer, OptionalInfoSerializer, \
    MatchSerializer
from django.db.models import Q
from rest_framework.authtoken.models import Token


class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('connect сработал')
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        print("Received data from client")
        data = json.loads(text_data).copy()
        longitude = data['longitude']
        latitude = data['latitude']
        print(f'Я принял координаты: широта - {longitude}, долгота - {latitude}')

        token = self.scope.get('cookies', {}).get('access_token')
        print(f'token - {token}')
        user = None  # Инициализация переменной user
        if token:
            user = await get_user_from_jwt(token)
            print(f"Пользователь: {user}")
        #
        if user.is_authenticated:
            await save_location(longitude=longitude, latitude=latitude, user=user)

        # Отправляем обратно
        await self.send(text_data=json.dumps({
            'longitude': longitude,
            'latitude': latitude,
        }))


class MaybeMatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        await self.accept()  # Принять соединение

        matches_data = await self.get_matches()
        await self.send(matches_data)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "authenticate":
            token_key = data.get("token")
            user = await self.get_user_from_token(token_key)  # Получаем пользователя асинхронно

            if user:
                self.user = user
                await self.send(json.dumps({"type": "authenticated", "message": "Аутентификация успешна"}))
                matches_data = await self.get_matches()
                await self.send(matches_data)

            elif data.get("type") == "match_action":  # логика при нажатии на любую из кнопок maybematch
                matches_data = await self.get_matches()
                await self.send(matches_data)
            else:
                await self.send(json.dumps({"type": "error", "message": "Неверный токен"}))
                await self.close()
        else:
            await self.send(json.dumps({"type": "error", "message": "Пользователь не аутентифицирован"}))



    async def disconnect(self, close_code):
        print(f"WebSocket отключен с кодом: {close_code}")
        raise StopConsumer()

    @sync_to_async
    def get_matches(self):
        params = self.filter_matches()  # Вызов асинхронной функции
        matches_data = []

        if params:
            seen = set()

            for match in params:
                match_id = (match.user_1.id, match.user_2.id)

                if match_id in seen:
                    continue
                else:
                    seen.add(match_id)
                    search_name, is_it_him = (match.session_2, match.user_1) if match.user_2 == self.user else (
                        match.session_1, match.user_2)

                    match_info = {
                        'maybematch': MaybeMatchSerializer(match).data,
                        'search_name': SessionSerializer(search_name).data,
                        'is_it_him': CustomUserSerializer(is_it_him).data,
                        'his_picture': OptionalInfoSerializer(is_it_him.optionalinfo).data,
                        'about_him': OptionalInfoSerializer(is_it_him.optionalinfo).data,
                    }

                    matches_data.append(match_info)

            data = {
                'count': len(matches_data),  # Количество уникальных матчей
                'matches': matches_data,  # Сами матчи
            }
        else:
            data = {
                'count': 0,
                'matches': []
            }

        return json.dumps(data)

    def filter_matches(self):
        user_id = self.user.id  # Здесь мы получаем ID пользователя
        return MaybeMatch.objects.filter(
            (Q(id_confirmed_by_user1=False) & Q(user_1=user_id)) |
            (Q(id_confirmed_by_user2=False) & Q(user_2=user_id))
        )

    @sync_to_async
    def get_user_from_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None


class MatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        await self.accept()

        self.loop = asyncio.get_event_loop()

        # Сразу запускаем проверку обновлений при подключении
        await self.check_for_updates()

    async def receive(self, text_data=None):
        data = json.loads(text_data)

        if data.get("type") == "authenticate":
            token_key = data.get("token")
            user = await self.get_user_from_token(token_key)

            if user:
                self.user = user
                await self.send(json.dumps({"type": "authenticated", "message": "Аутентификация успешна"}))
            else:
                await self.send(json.dumps({"type": "error", "message": "Неверный токен"}))
                await self.close()
        else:
            await self.send(json.dumps({"type": "error", "message": "Пользователь не аутентифицирован"}))

    @sync_to_async
    def get_and_process_matches(self):
        maybe_matches = self.get_maybe_matches()

        if maybe_matches:
            for match in maybe_matches:
                match_exists = self.match_exists(match)

                if not match_exists:
                    # Создаем новый матч
                    self.create_match(match)

                    # Обновляем статус сессий
                    self.update_session_status(match)

            # Получаем и отправляем данные о матчах текущего пользователя
            matches_data = self.get_user_matches()
            print(len(matches_data))
            return json.dumps({
                'status': status.HTTP_200_OK,
                'matches': matches_data,
                'mcount': len(matches_data),
            })
        else:
            return json.dumps({
                'status': status.HTTP_404_NOT_FOUND,
                'detail': 'No matches found',
            })

    def get_maybe_matches(self):
        user_id = self.user.id
        return MaybeMatch.objects.filter(
            (Q(user_1=user_id) | Q(user_2=user_id)) &
            Q(id_confirmed_by_user1=True) &
            Q(id_confirmed_by_user2=True)
        )

    def match_exists(self, maybe_match):
        return Match.objects.filter(
            user_1=maybe_match.user_1,
            session_1=maybe_match.session_1,
            user_2=maybe_match.user_2,
            session_2=maybe_match.session_2
        ).exists()

    def create_match(self, maybe_match):
        Match.objects.create(
            user_1=maybe_match.user_1,
            session_1=maybe_match.session_1,
            user_2=maybe_match.user_2,
            session_2=maybe_match.session_2,
        )

    def update_session_status(self, maybe_match):
        maybe_match.session_1.is_active = False
        maybe_match.session_1.save()
        maybe_match.session_2.is_active = False
        maybe_match.session_2.save()

    def get_user_matches(self):
        user_id = self.user.id
        matches = Match.objects.filter(
            Q(user_1=user_id) | Q(user_2=user_id)
        )
        serializer = MatchSerializer(matches, many=True)
        return serializer.data

    @sync_to_async
    def get_user_from_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    def schedule_next_check(self, delay=10):
        self.scheduled_task = self.loop.call_later(delay, asyncio.create_task, self.check_for_updates())

    async def check_for_updates(self):
        try:
            # Получаем и отправляем данные о матчах
            match_data = await self.get_and_process_matches()
            await self.send(text_data=match_data)

        except Exception as e:
            print(f"Ошибка при проверке обновлений: {e}")

        # Планируем следующую проверку через 10 секунд
        self.schedule_next_check()

    async def disconnect(self, close_code):
        # Отменяем запланированные задачи при отключении
        if hasattr(self, 'scheduled_task'):
            self.scheduled_task.cancel()
        print(f"WebSocket отключен с кодом: {close_code}")
        raise StopConsumer()
