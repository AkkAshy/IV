from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework import generics

from university.models import Building, Floor, Room
from .models import Equipment
from .serializers import EquipmentSerializer
from .filters import EquipmentFilter


class EquipmentStatisticsView(APIView):
    """
    View to get statistics about equipment distribution and status.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all equipment for the current user
        equipment = Equipment.objects.filter(author=request.user)

        # Building statistics
        building_stats = []
        buildings = Building.objects.all()

        for building in buildings:
            building_equipment = equipment.filter(room__building=building)

            # Count by status
            working_count = building_equipment.filter(status='WORKING').count()
            needs_repair_count = building_equipment.filter(status='NEEDS_REPAIR').count()
            disposed_count = building_equipment.filter(status='DISPOSED').count()
            new_count = building_equipment.filter(status='NEW').count()

            # Add to stats
            building_stats.append({
                'building_id': building.id,
                'building_name': building.name,
                'total_equipment': building_equipment.count(),
                'status_breakdown': {
                    'working': working_count,
                    'needs_repair': needs_repair_count,
                    'disposed': disposed_count,
                    'new': new_count
                }
            })

        # Floor statistics
        floor_stats = []
        floors = Floor.objects.all()

        for floor in floors:
            floor_equipment = equipment.filter(room__floor=floor)

            # Count by status
            working_count = floor_equipment.filter(status='WORKING').count()
            needs_repair_count = floor_equipment.filter(status='NEEDS_REPAIR').count()
            disposed_count = floor_equipment.filter(status='DISPOSED').count()
            new_count = floor_equipment.filter(status='NEW').count()

            # Add to stats
            floor_stats.append({
                'floor_id': floor.id,
                'floor_number': floor.number,
                'building_name': floor.building.name,
                'total_equipment': floor_equipment.count(),
                'status_breakdown': {
                    'working': working_count,
                    'needs_repair': needs_repair_count,
                    'disposed': disposed_count,
                    'new': new_count
                }
            })

        # Room statistics
        room_stats = []
        rooms = Room.objects.all()

        for room in rooms:
            room_equipment = equipment.filter(room=room)

            # Count by status
            working_count = room_equipment.filter(status='WORKING').count()
            needs_repair_count = room_equipment.filter(status='NEEDS_REPAIR').count()
            disposed_count = room_equipment.filter(status='DISPOSED').count()
            new_count = room_equipment.filter(status='NEW').count()

            # Add to stats
            room_stats.append({
                'room_id': room.id,
                'room_number': room.number,
                'floor_number': room.floor.number,
                'building_name': room.building.name,
                'total_equipment': room_equipment.count(),
                'status_breakdown': {
                    'working': working_count,
                    'needs_repair': needs_repair_count,
                    'disposed': disposed_count,
                    'new': new_count
                }
            })

        # Overall status statistics
        total_equipment = equipment.count()
        working_count = equipment.filter(status='WORKING').count()
        needs_repair_count = equipment.filter(status='NEEDS_REPAIR').count()
        disposed_count = equipment.filter(status='DISPOSED').count()
        new_count = equipment.filter(status='NEW').count()

        overall_stats = {
            'total_equipment': total_equipment,
            'status_breakdown': {
                'working': working_count,
                'needs_repair': needs_repair_count,
                'disposed': disposed_count,
                'new': new_count
            },
            'status_percentage': {
                'working': round(working_count / total_equipment * 100, 2) if total_equipment > 0 else 0,
                'needs_repair': round(needs_repair_count / total_equipment * 100, 2) if total_equipment > 0 else 0,
                'disposed': round(disposed_count / total_equipment * 100, 2) if total_equipment > 0 else 0,
                'new': round(new_count / total_equipment * 100, 2) if total_equipment > 0 else 0
            }
        }

        # Equipment by type
        equipment_by_type = []
        types = equipment.values('type__name').annotate(count=Count('id'))

        for type_data in types:
            type_name = type_data['type__name']
            type_count = type_data['count']

            type_equipment = equipment.filter(type__name=type_name)

            # Count by status
            working_count = type_equipment.filter(status='WORKING').count()
            needs_repair_count = type_equipment.filter(status='NEEDS_REPAIR').count()
            disposed_count = type_equipment.filter(status='DISPOSED').count()
            new_count = type_equipment.filter(status='NEW').count()

            equipment_by_type.append({
                'type_name': type_name,
                'total_count': type_count,
                'status_breakdown': {
                    'working': working_count,
                    'needs_repair': needs_repair_count,
                    'disposed': disposed_count,
                    'new': new_count
                }
            })

        # Return all statistics
        return Response({
            'overall_stats': overall_stats,
            'equipment_by_type': equipment_by_type,
            'building_stats': building_stats,
            'floor_stats': floor_stats,
            'room_stats': room_stats
        })


class EquipmentFilter(filters.FilterSet):
    building = filters.NumberFilter(field_name='room__building')
    floor = filters.NumberFilter(field_name='room__floor')
    room = filters.NumberFilter(field_name='room')
    type = filters.NumberFilter(field_name='type')
    status = filters.ChoiceFilter(choices=Equipment.STATUS_CHOICES)
    created_from = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    is_active = filters.BooleanFilter(field_name='is_active')
    author = filters.NumberFilter(field_name='author')

    class Meta:
        model = Equipment
        fields = ['building', 'floor', 'room', 'type', 'status', 'created_from', 'created_to', 'is_active', 'author']


class FilteredEquipmentListView(generics.ListAPIView):
    """
    View to get a filtered list of equipment.
    """
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = EquipmentFilter

    def get_queryset(self):
        # Return only equipment owned by the current user
        return Equipment.objects.filter(author=self.request.user)




