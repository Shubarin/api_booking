import coreapi
import django_filters
from django_filters.rest_framework import FilterSet

from .models import Room


class RoomFilterBackend(FilterSet):
    datetime_from = django_filters.DateTimeFilter(name='datetime_from')
    datetime_to = django_filters.DateTimeFilter(name='datetime_to')

    class Meta:
        fields = ['datetime_from', 'datetime_to']
        model = Room

    def get_schema_fields(self, view):
        return [
            coreapi.Field(
                name='datetime_from',
                location='query',
                required=False,
                type='string',
                description='Выбирает время начала выборки. Строка в формате ISO',
                example='2021-01-20 00:00:00',
            ),
            coreapi.Field(
                name='datetime_to',
                location='query',
                required=False,
                type='string',
                description='Выбирает время начала выборки. Строка в формате ISO',
                example='2021-01-20 00:00:00',
            ),
        ]
