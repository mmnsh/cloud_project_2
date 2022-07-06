import django.utils.timezone
from django.db import models


# Create your models here.

class AirportManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('city')


class FlightsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('origin_airport', 'dest_airport', 'airplane', 'carrier')


class ReserveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('flight')


class AirPlain(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()


class Carrier(models.Model):
    name = models.CharField(max_length=100)
    rating = models.FloatField(default=0)


class City(models.Model):
    name = models.CharField(max_length=100)


class Airport(models.Model):
    abbr = models.CharField(max_length=5)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    objects = AirportManager()


class Flight(models.Model):
    date_time = models.DateTimeField()
    price = models.FloatField()
    class_type = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')])
    origin_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='origin_airport')
    dest_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='dest_airport')
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    airplane = models.ForeignKey(AirPlain, on_delete=models.CASCADE)

    objects = FlightsManager()


class Reserve(models.Model):
    submit_date = models.DateTimeField(auto_now_add=True)
    user_id = models.BigIntegerField()
    flight = models.ForeignKey(Flight, on_delete=models.DO_NOTHING)

    objects = ReserveManager()

    class Meta:
        unique_together = ['user_id', 'flight']
