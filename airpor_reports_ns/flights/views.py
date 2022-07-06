import base64
import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from io import BytesIO

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
import matplotlib.pyplot as plt
import numpy as np
from django.db import connections
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from .models import Flight

min_date = datetime.datetime(year=2020, month=1, day=1, hour=0, minute=0, second=0)
max_date = datetime.datetime(year=2022, month=1, day=1, hour=0, minute=0, second=0)


class DateFilteredView(APIView):
    authentication_classes = [JSONWebTokenAuthentication]

    def _get_dates(self):
        try:
            year = self.request.query_params.get('year', 2020)
            month = self.request.query_params.get('month', 1)
            month = int(month or 1)
            year = int(year or 2020)
            self.duration = int(self.request.query_params.get('duration', 1))
            user_date = datetime.datetime(year=year, month=month, day=1)
            final_date = user_date + relativedelta(months=self.duration)
            self.date_query = " WHERE ff.date_time BETWEEN '{start_date}' AND '{end_date}' ".format(
                start_date=user_date,
                end_date=final_date)
            if user_date < min_date or final_date > max_date:
                raise Exception('')
        except Exception as e:
            raise ValidationError('Invalid Input')

    def _create_city_query(self, airport_type: str, cities: list):
        self.query += '`fc`.`name` as title '
        self.group_by += '`fc`.`name` '
        city_join = ' JOIN flights_city fc on fp.city_id = fc.id '
        city_query = " AND `fc`.`name` IN ('{cities}')".format(cities="','".join(cities))
        airport_join = ' JOIN flights_airport fp on ff.{airport_type}_id = fp.id'.format(airport_type=airport_type)
        self.query += ' FROM flights_flight ff' + airport_join + city_join + self.date_query + city_query

    def _create_airport_query(self, airport_type: str, airports: list):
        self.query += 'fp.abbr as title '
        self.group_by += 'fp.abbr'
        airport_join = ' JOIN flights_airport fp on ff.{airport_type}_id = fp.id'.format(airport_type=airport_type)
        airport_query = " AND fp.abbr IN ('{airports}')".format(airports="','".join(airports))
        self.query += ' FROM flights_flight ff' + airport_join + self.date_query + airport_query

    def _create_carrier_query(self, carriers: list):
        self.query += '`fc`.`name` as title'
        self.group_by += '`fc`.`name`'
        reserve_join = ' Join flights_reserve as fr on fr.flight_id = ff.id'
        carrier_join = ' JOIN flights_carrier fc on fc.id = ff.carrier_id'
        carrier_query = " AND `fc`.`name` IN ('{carriers_str}')".format(carriers_str="','".join(carriers))
        self.query += ' FROM flights_flight ff' + reserve_join + carrier_join + self.date_query + carrier_query

    def _create_airplanes_query(self, airplanes: list):
        self.query += '`fa`.`name` as title'
        self.group_by += '`fa`.`name`'
        airplane_join = ' JOIN flights_airplain fa on fa.id = ff.airplane_id'
        airplane_query = " AND `fa`.`name` IN ('{airplanes_str}') ".format(airplanes_str="','".join(airplanes))
        self.query += ' FROM flights_flight ff' + airplane_join + self.date_query + airplane_query

    def _get_query(self, city: list = None, airport: list = None, carrier: list = None, airplane: list = None,
                   in_or_out='in'):
        if city is None and airport is None and carrier is None and airplane is None:
            raise ValidationError('Invalid Query Parameters')
        self._get_dates()
        self.query = 'select year(date_time) as d_year, month(date_time) as d_month, count(*) as item_count, '
        self.group_by = ' group by year(date_time), month(date_time), '
        if in_or_out == 'in':
            airport_type = 'dest_airport'
            key = "incoming"
        else:
            airport_type = 'origin_airport'
            key = "outgoing"
        if city:
            self.title = 'Number of of {key} flights from {cities} cities in {duration} month(s)'.format(key=key,
                                                                                                         cities=', '.join(
                                                                                                             city),
                                                                                                         duration=self.duration)
            self._create_city_query(airport_type, city)
        elif airport:
            self.title = 'Number of of {key} flights from {airports} cities in {duration} month(s)'.format(key=key,
                                                                                                           airports=', '.join(
                                                                                                               airport),
                                                                                                           duration=self.duration)
            self._create_airport_query(airport_type, airport)
        elif carrier:
            self.title = 'Total sale of {carriers} in {duration} month(s)'.format(duration=self.duration,
                                                                                  carriers=', '.join(carrier))
            self._create_carrier_query(carrier)
        elif airplane:
            self.title = 'Flights done by {airplanes} in {duration} months(s)'.format(duration=self.duration,
                                                                                      airplanes=', '.join(airplane))
            self._create_airplanes_query(airplane)
        self.query += self.group_by
        self.query += ' order by year(date_time), month(date_time)'

    def _get_data(self):
        print(self.query)
        with connections['flights'].cursor() as cursor:
            cursor.execute(self.query)
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    def _get_plot(self):
        data = self._get_data()
        labels = set()
        items = defaultdict(list)
        for d in data:
            labels.add(f"{d['d_year']}/{d['d_month']}")
            items[d['title']].append(d['item_count'])
        labels = list(labels)
        ln_lbl = len(labels)
        x = np.arange(ln_lbl)
        width = 1.0 / (ln_lbl * 2 + 1)
        rects = list()
        fig, ax = plt.subplots()
        i = 0
        for key, value in items.items():
            rects.append(ax.bar(x + width * i, value, width, label=key))
            i += 1
        plt.xlabel('Dates')
        ax.set_title(self.title)
        plt.ylabel('Count')
        ax.set_xticks(x + width, labels)
        ax.legend()
        for rect in rects:
            ax.bar_label(rect, padding=5)
        fig.tight_layout()
        tmp_file = BytesIO()
        fig.savefig(tmp_file, format='png')
        return tmp_file.getvalue()


class CityAirportTrafficView(DateFilteredView):

    def get(self, request):
        cities = self.request.query_params.get('cities', None)
        if cities:
            cities = [str(city).strip() for city in cities.split(',')]
        airports = self.request.query_params.get('airports', None)
        if airports:
            airports = [str(air).strip() for air in airports.split(',')]
        in_or_out = self.request.query_params.get('type', 'out')
        self._get_query(cities, airports, in_or_out)
        plot = self._get_plot()
        return HttpResponse(content_type="image/png", content=plot)


class CarrierTotalSalesView(DateFilteredView):

    def get(self, request):
        carriers = self.request.query_params.get('carriers', '')
        carriers = [str(carr).strip() for carr in carriers.split(',')]
        self._get_query(carrier=carriers)
        plot = self._get_plot()
        return HttpResponse(content_type="image/png", content=plot)


class AirplaneFliesView(DateFilteredView):

    def get(self, request):
        airplanes = self.request.query_params.get('airplanes', '')
        airplanes = [str(airp).strip() for airp in airplanes.split(',')]
        self._get_query(airplane=airplanes)
        plot = self._get_plot()
        return HttpResponse(content_type="image/png", content=plot)
