from django.contrib import admin
from .models import CustomUser, Marker, MarkerHistory, Match, Message, Session, OptionalInfo

admin.site.register(CustomUser)
admin.site.register(Marker)
admin.site.register(MarkerHistory)
admin.site.register(Match)
admin.site.register(Message)
admin.site.register(Session)
admin.site.register(OptionalInfo)