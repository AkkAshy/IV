# inventory/filters.py

from django_filters import rest_framework as filters
from django.db import models
from .models import Equipment

class EquipmentFilter(filters.FilterSet):
    """
    Filter class for Equipment model.
    Allows filtering by various fields including building, floor, room, type, status, etc.
    """
    building = filters.NumberFilter(field_name='room__building')
    floor = filters.NumberFilter(field_name='room__floor')
    room = filters.NumberFilter(field_name='room')
    type = filters.NumberFilter(field_name='type')
    status = filters.ChoiceFilter(choices=Equipment.STATUS_CHOICES)
    created_from = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    is_active = filters.BooleanFilter(field_name='is_active')
    author = filters.NumberFilter(field_name='author')

    # Additional filters for characteristics
    # Computer filters
    cpu = filters.CharFilter(field_name='computer_details__cpu', lookup_expr='icontains')
    ram = filters.CharFilter(field_name='computer_details__ram', lookup_expr='icontains')
    storage = filters.CharFilter(field_name='computer_details__storage', lookup_expr='icontains')
    has_keyboard = filters.BooleanFilter(field_name='computer_details__has_keyboard')
    has_mouse = filters.BooleanFilter(field_name='computer_details__has_mouse')

    # Printer filters
    printer_model = filters.CharFilter(field_name='printer_char__model', lookup_expr='icontains')
    printer_color = filters.BooleanFilter(field_name='printer_char__color')
    printer_duplex = filters.BooleanFilter(field_name='printer_char__duplex')

    # Router filters
    router_model = filters.CharFilter(field_name='router_char__model', lookup_expr='icontains')
    router_ports = filters.NumberFilter(field_name='router_char__ports')
    router_wifi = filters.CharFilter(field_name='router_char__wifi_standart', lookup_expr='icontains')

    # TV filters
    tv_model = filters.CharFilter(field_name='tv_char__model', lookup_expr='icontains')
    tv_screen_size = filters.CharFilter(field_name='tv_char__screen_size', lookup_expr='icontains')

    # Monitor filters
    monitor_size = filters.CharFilter(field_name='computer_details__monitor_size', lookup_expr='icontains')

    # Search filter for general text search
    search = filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """
        Search in name, description, and INN fields
        """
        return queryset.filter(
            models.Q(name__icontains=value) |
            models.Q(description__icontains=value) |
            models.Q(inn__icontains=value)
        )

    class Meta:
        model = Equipment
        fields = [
            'building', 'floor', 'room', 'type', 'status', 'created_from',
            'created_to', 'is_active', 'author', 'cpu', 'ram', 'storage',
            'has_keyboard', 'has_mouse', 'printer_model', 'printer_color',
            'printer_duplex', 'router_model', 'router_ports', 'router_wifi',
            'tv_model', 'tv_screen_size', 'monitor_size', 'search'
        ]