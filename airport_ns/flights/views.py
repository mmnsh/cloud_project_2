from django.http import HttpResponse
from django_filters import rest_framework as filters
from rest_framework import mixins
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from .serilizers import *


# Create your views here.


def insert_data(request):
    with open('/home/joker/Programming/Python/PycharmProjects/airport_ns/flights/planes.csv') as planes_str:
        for plane_str in planes_str:
            details = plane_str.split(',')
            AirPlain.objects.get_or_create(name=details[0].strip(), capacity=int(details[1].strip()))
    with open('/home/joker/Programming/Python/PycharmProjects/airport_ns/flights/carriers.csv') as carirers_str:
        for car_str in carirers_str:
            details = car_str.split(',')
            Carrier.objects.get_or_create(name=details[0].strip(), rating=float(details[1].strip()))
    with open('/home/joker/Programming/Python/PycharmProjects/airport_ns/flights/airports.csv') as airports_str:
        for airport_str in airports_str:
            details = airport_str.split(',')
            city, _ = City.objects.get_or_create(name=details[0].strip())
            Airport.objects.get_or_create(abbr=details[1].strip(), city=city)
    with open('/home/joker/Programming/Python/PycharmProjects/airport_ns/flights/flights.csv') as flights_str:
        for flight_str in flights_str:
            details = flight_str.split(',')
            origin_airport = Airport.objects.get(abbr=details[1].strip(), city__name=details[0].strip())
            dest_airport = Airport.objects.get(abbr=details[3].strip(), city__name=details[2].strip())
            date_time = details[4].strip()
            carrier = Carrier.objects.get(name=details[6].strip())
            price = float(details[5].strip())
            class_type = details[7].strip()
            airplain = AirPlain.objects.get(name=details[8].strip())
            Flight.objects.get_or_create(origin_airport=origin_airport, dest_airport=dest_airport,
                                         date_time=date_time,
                                         carrier=carrier, class_type=class_type, airplane=airplain, price=price)
    return HttpResponse()


class MyViewSet(mixins.CreateModelMixin,
                mixins.RetrieveModelMixin,
                mixins.DestroyModelMixin,
                mixins.ListModelMixin,
                GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `destroy()` and `list()` actions.
    """
    pass


class FlightsFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')
    after = filters.DateTimeFilter(field_name="date_time", lookup_expr='gte')
    before = filters.DateTimeFilter(field_name="date_time", lookup_expr='lte')
    out_city = filters.CharFilter(field_name="origin_airport__city__name", lookup_expr='contains')
    out_airport = filters.CharFilter(field_name="origin_airport__abbr", lookup_expr='contains')
    in_city = filters.CharFilter(field_name="dest_airport__city__name", lookup_expr='contains')
    in_airport = filters.CharFilter(field_name="dest_airport__abbr", lookup_expr='contains')
    airplane = filters.CharFilter(field_name="airplane__name", lookup_expr='contains')
    carrier = filters.CharFilter(field_name="carrier__name", lookup_expr='contains')

    class Meta:
        model = Flight
        fields = ['class_type', 'date_time', 'price']


class FlightsView(ListAPIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FlightSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FlightsFilter
    queryset = Flight.objects.all()


class CarrierAirplanesView(ListAPIView):
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FlightAirplanesSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = FlightsFilter

    def get_queryset(self):
        return Flight.objects.filter(carrier__name=self.kwargs['carrier']).values('airplane').distinct()


class ReserveView(MyViewSet):
    serializer_class = ReserveCreateSerializer
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.user.id
        return Reserve.objects.filter(user_id=user_id)
    
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = ReserveSerializer
        return super(ReserveView, self).retrieve(request, *args, **kwargs)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'kwargs': self.kwargs,
            'format': self.format_kwarg,
            'view': self
        }
