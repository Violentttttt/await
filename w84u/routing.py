from django.urls import path
from . import consumers

ws_urlpatterns = [
    path('ws/location/', consumers.LocationConsumer.as_asgi()),
    path('ws/maybematch/', consumers.MaybeMatchConsumer.as_asgi()),
    path('ws/match/', consumers.MatchConsumer.as_asgi()),
]
