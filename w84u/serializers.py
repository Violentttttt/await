from rest_framework import serializers
from w84u.models import CustomUser, Marker, MarkerHistory, Match, Message, Session, OptionalInfo, MaybeMatch, Geo
from django.contrib.gis.geos import Point


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'


class OptionalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionalInfo
        fields = '__all__'


class MarkerSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = Marker
        fields = ['id', 'user', 'location', 'type', 'created_at']

    def get_location(self, obj):
        if obj.location:
            return {
                'lat': obj.location.y,
                'lng': obj.location.x
            }
        return None

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)
        if 'latitude' in data and 'longitude' in data:
            internal_data['location'] = Point(data['longitude'], data['latitude'])
        return internal_data


class MarkerHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkerHistory
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'


class MaybeMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaybeMatch
        fields = '__all__'


class MatchSerializer(serializers.ModelSerializer):
    user_1 = CustomUserSerializer(read_only=True)
    user_2 = CustomUserSerializer(read_only=True)
    session_1 = SessionSerializer(read_only=True)
    session_2 = SessionSerializer(read_only=True)

    class Meta:
        model = Match
        fields = "__all__"


'''Костыль для страницы с историей'''


class HistoryMarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marker
        fields = ['location', 'type', 'created_at']


class HistorySerializer(serializers.ModelSerializer):
    red_marker = HistoryMarkerSerializer()
    blue_marker = HistoryMarkerSerializer()

    class Meta:
        model = Session
        fields = ['id', 'name', 'gender', 'date', 'datetime_range', 'red_marker', 'blue_marker', 'surname', 'is_active',
                  'created_at']


'''Костыль для страницы с историей'''


class GeoSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = Geo
        fields = ['user', 'recorded_at']

    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)
        if 'latitude' in data and 'longitude' in data:
            internal_data['location'] = Point(data['longitude'], data['latitude'])
        return internal_data
