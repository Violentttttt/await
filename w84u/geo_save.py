from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils import timezone
from w84u.models import Geo
from channels.db import database_sync_to_async


@database_sync_to_async
def save_location_sync(user, longitude, latitude):
    new_point = Point(longitude, latitude, srid=4326)

    # Получаем последнюю запись пользователя
    last_record = Geo.objects.filter(user=user).order_by('-recorded_at').first()

    if last_record:
        distance = last_record.location.distance(new_point)
        # Если расстояние больше 50 метров, сохраняем новую запись
        if distance >= D(m=50).m:
            Geo.objects.create(user=user, location=new_point, recorded_at=timezone.now())
    else:  # Если это первая запись
        Geo.objects.create(user=user, location=new_point, recorded_at=timezone.now())


async def save_location(user, longitude, latitude):
    await save_location_sync(user, longitude, latitude)
