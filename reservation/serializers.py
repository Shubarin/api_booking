from rest_framework import serializers

from .models import Reservation, Room, User


class ReservationSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        fields = '__all__'
        model = Reservation


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Room


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = User
