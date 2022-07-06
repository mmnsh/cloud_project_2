from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Reserve,
    Airport,
    AirPlain,
    Flight,
    City,
    Carrier,
)


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class AirportSerializer(serializers.ModelSerializer):
    city = CitySerializer()

    class Meta:
        model = Airport
        fields = '__all__'


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = '__all__'


class AirPlainSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirPlain
        fields = '__all__'


class FlightSerializer(serializers.ModelSerializer):
    origin_airport = AirportSerializer()
    dest_airport = AirportSerializer()
    carrier = CarrierSerializer()
    airplane = AirPlainSerializer()

    class Meta:
        model = Flight
        fields = '__all__'


class FlightAirplanesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = '__all__'

    def to_representation(self, instance):
        return AirPlainSerializer(AirPlain.objects.get(pk=instance['airplane'])).data


class ReserveSerializer(serializers.ModelSerializer):
    flight = FlightSerializer()

    class Meta:
        model = Reserve
        fields = ['flight', 'id']


class ReserveCreateSerializer(serializers.ModelSerializer):
    flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all())

    def validate(self, attrs):
        if attrs['flight'].airplane.capacity <= Reserve.objects.filter(flight=attrs['flight']).count():
            raise ValidationError('Maximum Capacity of Flight is Reached')
        return attrs

    def create(self, validated_data):
        instance, _ = Reserve.objects.get_or_create(flight=validated_data['flight'],
                                                    user_id=self.context['request'].user.id)
        return instance

    def to_representation(self, instance):
        return ReserveSerializer(instance).data

    class Meta:
        model = Reserve
        fields = ['flight']
