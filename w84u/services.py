from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from .Comparator import create_maybematch
from .models import Session, MaybeMatch, OptionalInfo, CustomUser , MaybeMatch
from django.http import HttpResponse
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q, F
from psycopg2.extras import DateTimeRange
from django.utils.dateparse import parse_datetime
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
@receiver(post_save, sender=Session)
def handle_session_save(sender, instance, created, **kwargs):
    if created:
        find_possible_matches(instance)

def find_possible_matches(session):

        try:
            exclude_session = session
            print(exclude_session)
            # exclude_session = Session.objects.filter(user=pk).latest('created_at')
            blue_marker = exclude_session.blue_marker
            red_marker = exclude_session.red_marker
            exclude_session_name = exclude_session.name
            exclude_session_surname = exclude_session.surname
            print(exclude_session_name)
            print(exclude_session_surname)
            users_surname = OptionalInfo.objects.filter(pk=session.user_id).values_list('surname', flat=True).first()
            print(users_surname)
            real_name = CustomUser.objects.filter(pk=session.user_id).values_list('real_name', flat=True).first()
            print(real_name)

        except Session.DoesNotExist:
            return print('Сессия не найдена')

        if blue_marker and red_marker:
            radius_km = 0.05  # 50 метров

            blue_point = GEOSGeometry(blue_marker.location)
            red_point = GEOSGeometry(red_marker.location)

            print("Blue point:", blue_point)
            print("Red point:", red_point)

            filtered_sessions_geo = Session.objects.annotate(
                distance_blue=Distance('blue_marker__location', red_point),
                distance_red=Distance('red_marker__location', blue_point)
            ).filter(
                distance_blue__lte=D(km=radius_km),
                distance_red__lte=D(km=radius_km)
            )

        if exclude_session.date is not None:
            filtered_by_datetime = filtered_sessions_geo.filter(
                Q(datetime_range__contains=exclude_session.date) | Q(date=exclude_session.date))
        elif exclude_session.datetime_range is not None:
            start_datetime = exclude_session.datetime_range.lower  # Начало диапазона
            end_datetime = exclude_session.datetime_range.upper  # Конец диапазона
            filtered_by_datetime = filtered_sessions_geo.filter(
                Q(datetime_range__overlap=exclude_session.datetime_range) | Q(date__range=(start_datetime, end_datetime)))


        if exclude_session_name is not '':
            filtered_by_datetime = filtered_by_datetime.filter(name=real_name)
            print('я прогнал по именам')

        if exclude_session.surname is not '':
            filtered_by_datetime = filtered_by_datetime.filter(surname=users_surname)
            print('я прогнал по фамилиям')

        filtered_sessions = filtered_by_datetime.filter(
            gender=exclude_session.user.gender
            # is_active=True
        ).exclude(pk=exclude_session.pk)
        print(filtered_sessions)

        for i in filtered_sessions:
            if exclude_session.user.id != i.user.id :
                print(f'Создание MaybeMatch между {exclude_session.user} и {i.user}')
                create_maybematch(exclude_session.user, exclude_session, i.user , i)

