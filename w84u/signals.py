import json

from django.dispatch import receiver
from django.db.models.signals import post_save
from w84u.models import MaybeMatch
from asgiref.sync import async_to_sync


def save_post(sender, instance, **kwargs):
    print('сигнал сработал')


post_save.connect(save_post, sender=MaybeMatch)


# @receiver(post_save, sender=MaybeMatch)
# def handle_match_save(sender, instance, created, **kwargs):
#     """
#     Обработчик сигнала для отправки обновлений при сохранении нового матча.
#     """
#     print('Сигнал сработал: новый матч добавлен или обновлен.')
#
#     # Проверяем, существует ли WebSocket-подключение для пользователей этого матча
#     if instance.user_1.id in active_connections:
#         consumer = active_connections[instance.user_1.id]
#         async_to_sync(consumer.send_update)(json.dumps({'message': 'Матч обновлен'}))  # Отправляем обновление
#
#     if instance.user_2.id in active_connections:
#         consumer = active_connections[instance.user_2.id]
#         async_to_sync(consumer.send_update)(json.dumps({'message': 'Матч обновлен'}))
#
#
# print(active_connections)
