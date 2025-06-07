# from rest_framework import generics
# from .models import University, Building, Faculty, Floor, Room, RoomHistory, FacultyHistory
# from .serializers import (UniversitySerializer, BuildingSerializer,
#                           FacultySerializer, FloorSerializer, RoomSerializer,
#                           FacultyMoveSerializer, RoomSplitSerializer, RoomMergeSerializer,
#                           RoomMoveSerializer, FacultySplitSerializer, FacultyMergeSerializer)
# from rest_framework.exceptions import PermissionDenied
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from .permissions import IsAdminUser
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from rest_framework import viewsets, mixins
# from django.db import transaction
# from rest_framework.decorators import action


# # Университеты
# class UniversityListCreateView(generics.ListCreateAPIView):
#     queryset = University.objects.all()
#     serializer_class = UniversitySerializer
#     permission_classes_by_action = {
#         'GET': [AllowAny],
#         'POST': [IsAuthenticated, IsAdminUser],
#     }

#     def get_permissions(self):
#         return [permission() for permission in self.permission_classes_by_action.get(self.request.method, [IsAuthenticated])]

# class UniversityDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = University.objects.all()
#     serializer_class = UniversitySerializer
#     permission_classes = [IsAuthenticated, IsAdminUser]


# # Корпуса
# class BuildingListCreateView(generics.ListCreateAPIView):
#     queryset = Building.objects.all()
#     serializer_class = BuildingSerializer
#     permission_classes = [IsAuthenticated]

# class BuildingDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Building.objects.all()
#     serializer_class = BuildingSerializer
#     permission_classes = [IsAuthenticated]

# # # Факультеты
# class FacultyListCreateView(generics.ListCreateAPIView):
#     queryset = Faculty.objects.all()
#     serializer_class = FacultySerializer
#     permission_classes = [IsAuthenticated]

# class FacultyDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Faculty.objects.all()
#     serializer_class = FacultySerializer
#     permission_classes = [IsAuthenticated]

# # Этажи
# class FloorListCreateView(generics.ListCreateAPIView):
#     queryset = Floor.objects.all()
#     serializer_class = FloorSerializer
#     permission_classes = [IsAuthenticated]

# class FloorDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Floor.objects.all()
#     serializer_class = FloorSerializer
#     permission_classes = [IsAuthenticated]

# class FloorByBuildingView(generics.ListAPIView):
#     serializer_class = FloorSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Floor.objects.filter(building_id=self.kwargs['building_pk'])


# # Кабинеты
# class RoomListCreateView(generics.ListCreateAPIView):
#     queryset = Room.objects.all()
#     serializer_class = RoomSerializer
#     permission_classes = [IsAuthenticated]
#     permission_classes_by_action = {
#         'GET': [IsAuthenticated],
#         'POST': [IsAuthenticated, IsAdminUser],
#     }

#     def get_permissions(self):
#         return [permission() for permission in self.permission_classes_by_action.get(self.request.method, [])]

# class RoomDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Room.objects.all()
#     serializer_class = RoomSerializer
#     permission_classes = [IsAuthenticated]

#     def get_permissions(self):
#         if self.request.method in ['PUT', 'PATCH', 'DELETE']:
#             return [IsAdminUser()]
#         return super().get_permissions()




# from rest_framework import status
# class RoomListByBuildingView(APIView):
#     def get(self, request):
#         building_id = request.query_params.get('building_id')
#         if not building_id:
#             return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

#         rooms = Room.objects.filter(building_id=building_id)
#         serializer = RoomSerializer(rooms, many=True)
#         return Response(serializer.data)


# class RoomViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
#     queryset = Room.objects.select_related('building', 'floor')
#     serializer_class = RoomSerializer
#     permission_classes = [IsAuthenticated]

#     def get_serializer_class(self):
#         if self.action == 'split':
#             return RoomSplitSerializer
#         elif self.action == 'merge':
#             return RoomMergeSerializer
#         elif self.action == 'move':
#             return RoomMoveSerializer
#         return RoomSerializer

#     def update(self, request, *args, **kwargs):
#         room = self.get_object()
#         serializer = self.get_serializer(room, data=request.data, partial=True)
#         if serializer.is_valid():
#             old_data = RoomSerializer(room).data
#             serializer.save()
#             RoomHistory.objects.create(
#                 room=room,
#                 action='Updated',
#                 description=f'Updated from {old_data} to {serializer.data}'
#             )
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=['post'])
#     @transaction.atomic
#     def split(self, request, pk=None):
#         room = get_object_or_404(Room, pk=pk)
#         serializer = self.get_serializer(data=request.data, context={'room': room})
#         if serializer.is_valid():
#             new_rooms = serializer.save()
#             return Response(RoomSerializer(new_rooms, many=True).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['post'])
#     @transaction.atomic
#     def merge(self, request):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             new_room = serializer.save()
#             return Response(RoomSerializer(new_room).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=['post'])
#     @transaction.atomic
#     def move(self, request, pk=None):
#         room = get_object_or_404(Room, pk=pk)
#         serializer = self.get_serializer(data=request.data, context={'room': room})
#         if serializer.is_valid():
#             updated_room = serializer.update(room, serializer.validated_data)
#             return Response(RoomSerializer(updated_room).data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# class FacultyViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
#     queryset = Faculty.objects.select_related('building', 'floor')
#     serializer_class = FacultySerializer
#     permission_classes = [IsAuthenticated]

#     def get_serializer_class(self):
#         if self.action == 'split':
#             return FacultySplitSerializer
#         elif self.action == 'merge':
#             return FacultyMergeSerializer
#         elif self.action == 'move':
#             return FacultyMoveSerializer
#         return FacultySerializer

#     def update(self, request, *args, **kwargs):
#         faculty = self.get_object()
#         serializer = self.get_serializer(faculty, data=request.data, partial=True)
#         if serializer.is_valid():
#             old_data = FacultySerializer(faculty).data
#             serializer.save()
#             FacultyHistory.objects.create(
#                 faculty=faculty,
#                 action='Updated',
#                 description=f'Updated from {old_data} to {serializer.data}'
#             )
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=['post'])
#     @transaction.atomic
#     def split(self, request, pk=None):
#         faculty = get_object_or_404(Faculty, pk=pk)
#         serializer = self.get_serializer(data=request.data, context={'faculty': faculty})
#         if serializer.is_valid():
#             new_faculties = serializer.save()
#             return Response(FacultySerializer(new_faculties, many=True).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=['post'])
#     @transaction.atomic
#     def merge(self, request):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             new_faculty = serializer.save()
#             return Response(FacultySerializer(new_faculty).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=['post'])
#     @transaction.atomic
#     def move(self, request, pk=None):
#         faculty = get_object_or_404(Faculty, pk=pk)
#         serializer = self.get_serializer(data=request.data, context={'faculty': faculty})
#         if serializer.is_valid():
#             updated_faculty = serializer.update(faculty, serializer.validated_data)
#             return Response(FacultySerializer(updated_faculty).data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import generics
from .models import University, Building, Faculty, Floor, Room, RoomHistory, FacultyHistory
from .serializers import (UniversitySerializer, BuildingSerializer,
                          FacultySerializer, FloorSerializer, RoomSerializer,
                          FacultyMoveSerializer, RoomSplitSerializer, RoomMergeSerializer,
                          RoomMoveSerializer, FacultySplitSerializer, FacultyMergeSerializer,
                          RoomLinkSerializer)
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from django.db import transaction
from rest_framework.decorators import action
from user.models import UserAction
from user.serializers import UserActionSerializer


# Университеты
class UniversityListCreateView(generics.ListCreateAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes_by_action = {
        'GET': [AllowAny],
        'POST': [IsAuthenticated, IsAdminUser],
    }

    def get_permissions(self):
        return [permission() for permission in self.permission_classes_by_action.get(self.request.method, [IsAuthenticated])]

class UniversityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


# Корпуса
class BuildingListCreateView(generics.ListCreateAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]



class BuildingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]

# # Факультеты
class FacultyListCreateView(generics.ListCreateAPIView):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [IsAuthenticated]

class FacultyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [IsAuthenticated]

# Этажи
class FloorListCreateView(generics.ListCreateAPIView):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsAuthenticated]

class FloorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [IsAuthenticated]

class FloorByBuildingView(generics.ListAPIView):
    serializer_class = FloorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        building_id = self.kwargs.get('building_pk')
        return Floor.objects.filter(building_id=building_id)


# Кабинеты
class RoomListCreateView(generics.ListCreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    permission_classes_by_action = {
        'GET': [IsAuthenticated],
        'POST': [IsAuthenticated, IsAdminUser],
    }

    def get_permissions(self):
        return [permission() for permission in self.permission_classes_by_action.get(self.request.method, [])]

    def perform_create(self, serializer):
        # Используем transaction для атомарности
        with transaction.atomic():
            room = serializer.save(author=self.request.user)
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_ROOM',
                description=f"Создан кабинет: {room.name}"
            )

class RoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return super().get_permissions()




from rest_framework import status
class RoomListByBuildingView(APIView):
    def get(self, request):
        building_id = request.query_params.get('building_id')
        if not building_id:
            return Response({'error': 'building_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        rooms = Room.objects.filter(building_id=building_id)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)


class RoomViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Room.objects.select_related('building', 'floor')
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'split':
            return RoomSplitSerializer
        elif self.action == 'merge':
            return RoomMergeSerializer
        elif self.action == 'move':
            return RoomMoveSerializer
        return RoomSerializer

    def update(self, request, *args, **kwargs):
        room = self.get_object()
        serializer = self.get_serializer(room, data=request.data, partial=True)
        if serializer.is_valid():
            old_data = RoomSerializer(room).data
            serializer.save()
            RoomHistory.objects.create(
                room=room,
                action='Updated',
                description=f'Updated from {old_data} to {serializer.data}'
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def split(self, request, pk=None):
        room = get_object_or_404(Room, pk=pk)
        serializer = self.get_serializer(data=request.data, context={'room': room})
        if serializer.is_valid():
            new_rooms = serializer.save()
            return Response(RoomSerializer(new_rooms, many=True).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def merge(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_room = serializer.save()
            return Response(RoomSerializer(new_room).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    @transaction.atomic

    def move(self, request, pk=None):
        room = get_object_or_404(Room, pk=pk)
        serializer = self.get_serializer(data=request.data, context={'room': room})
        if serializer.is_valid():
            updated_room = serializer.update(room, serializer.validated_data)
            return Response(RoomSerializer(updated_room).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        with transaction.atomic():
            room = serializer.save(author=self.request.user)
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_ROOM',
                description=f"Создан кабинет: {room.name}"
            )



    def perform_destroy(self, instance):
        with transaction.atomic():
            UserAction.objects.create(
                user=self.request.user,
                action_type='DELETE_ROOM',
                description=f"Удалён кабинет: {instance.name}"
            )
            instance.delete()

    @action(detail=False, methods=['get'], url_path='my-actions')
    def my_actions(self, request):
        actions = UserAction.objects.filter(user=self.request.user, description__contains="кабинет").order_by('-created_at')
        serializer = UserActionSerializer(actions, many=True)
        return Response(serializer.data)




class FacultyViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Faculty.objects.select_related('building', 'floor')
    serializer_class = FacultySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'split':
            return FacultySplitSerializer
        elif self.action == 'merge':
            return FacultyMergeSerializer
        elif self.action == 'move':
            return FacultyMoveSerializer
        return FacultySerializer

    def update(self, request, *args, **kwargs):
        faculty = self.get_object()
        serializer = self.get_serializer(faculty, data=request.data, partial=True)
        if serializer.is_valid():
            old_data = FacultySerializer(faculty).data
            serializer.save()
            FacultyHistory.objects.create(
                faculty=faculty,
                action='Updated',
                description=f'Updated from {old_data} to {serializer.data}'
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def split(self, request, pk=None):
        faculty = get_object_or_404(Faculty, pk=pk)
        serializer = self.get_serializer(data=request.data, context={'faculty': faculty})
        if serializer.is_valid():
            new_faculties = serializer.save()
            return Response(FacultySerializer(new_faculties, many=True).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def merge(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            new_faculty = serializer.save()
            return Response(FacultySerializer(new_faculty).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def move(self, request, pk=None):
        faculty = get_object_or_404(Faculty, pk=pk)
        serializer = self.get_serializer(data=request.data, context={'faculty': faculty})
        if serializer.is_valid():
            updated_faculty = serializer.update(faculty, serializer.validated_data)
            return Response(FacultySerializer(updated_faculty).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get_queryset(self):
        print('Фильтрация активна')
        queryset = Faculty.objects.select_related('building', 'floor')
        building_id = self.request.query_params.get('building_id')
        floor_id = self.request.query_params.get('floor_id')
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        if floor_id:
            queryset = queryset.filter(floor_id=floor_id)
        return queryset


class RoomLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        room = get_object_or_404(Room, id=pk)
        serializer = RoomLinkSerializer(room, context={'request': request})
        return Response(serializer.data)

