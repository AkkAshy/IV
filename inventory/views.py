from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django.http import JsonResponse
from collections import defaultdict
from django.shortcuts import render, redirect
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .qr_serializations import QRScanSerializer
from rest_framework.exceptions import NotFound
from university.models import Room, Building
from university.serializers import RoomSerializer
from user.models import UserAction
from user.serializers import UserActionSerializer
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import qrcode
from django.http import HttpResponse
import os
from django.conf import settings


from university.models import Room, Building
from university.serializers import RoomSerializer


from user.models import UserAction
from user.serializers import UserActionSerializer


from .models import (EquipmentType, ContractDocument, Equipment,
                     ComputerDetails, MovementHistory, ComputerSpecification,
                     TVChar, ExtenderChar, RouterChar, PrinterChar,
                     PrinterSpecification, ExtenderSpecification,
                     RouterSpecification, TVSpecification,
                    WhiteboardSpecification, WhiteboardChar,
                    ProjectorChar, ProjectorSpecification,
                    NotebookChar, NotebookSpecification,
                    MonoblokChar, MonoblokSpecification, Repair, Disposal
)

from .serializers import (
    EquipmentTypeSerializer, ContractDocumentSerializer, EquipmentSerializer,
    ComputerDetailsSerializer, MovementHistorySerializer, ComputerSpecificationSerializer,
    MoveEquipmentSerializer, BulkEquipmentSerializer, BulkEquipmentInnUpdateSerializer,
    PrinterCharSerializer, ExtenderCharSerializer, TVCharSerializer, RouterCharSerializer,
    PrinterSpecificationSerializer, ExtenderSpecificationSerializer,
    RouterSpecificationSerializer, TVSpecificationSerializer,
    MonoblokCharSerializer, MonoblokSpecificationSerializer,
    NotebookCharSerializer, NotebookSpecificationSerializer,
    ProjectorCharSerializer, ProjectorSpecificationSerializer,
    WhiteboardCharSerializer, WhiteboardSpecificationSerializer,
    EquipmentFromLinkSerializer,
    RepairSerializer, DisposalSerializer, EquipmentNameSerializer,
    CustomEquipmentSerializer
)
from .pagination import ContractPagination, CustomPagination

from .permissions import IsAdminOrOwner



from django.urls import reverse

class SpecificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]  # Гарантируем, что пользователь аутентифицирован

    def get_queryset(self, model):
        # Фильтруем только записи текущего пользователя
        return model.objects.filter(author=self.request.user)

    @action(detail=False, methods=['get'], url_path='specification-count')
    def specification_count(self, request):
        # Проверка аутентификации (на всякий случай, хотя IsAuthenticated уже есть)
        if not request.user.is_authenticated:
            return Response({"error": "Пользователь не аутентифицирован"}, status=401)

        # Список всех моделей Specification
        specification_models = [
            {'model': ComputerSpecification, 'name': 'ComputerSpecification'},
            {'model': PrinterSpecification, 'name': 'PrinterSpecification'},
            {'model': ExtenderSpecification, 'name': 'ExtenderSpecification'},
            {'model': RouterSpecification, 'name': 'RouterSpecification'},
            {'model': TVSpecification, 'name': 'TVSpecification'},
            {'model': WhiteboardSpecification, 'name': 'WhiteboardSpecification'},
            {'model': ProjectorSpecification, 'name': 'ProjectorSpecification'},
            {'model': NotebookSpecification, 'name': 'NotebookSpecification'},
            {'model': MonoblokSpecification, 'name': 'MonoblokSpecification'},
        ]

        # Результат
        result = {}

        for spec in specification_models:
            model = spec['model']
            model_name = spec['name']
            # Подсчитываем общее количество записей для текущего пользователя
            count = self.get_queryset(model).count()
            if count > 0:  # Добавляем только модели с записями
                result[model_name] = count

        return Response(result if result else {}, status=200)


class EquipmentFromLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EquipmentFromLinkSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            room_data = serializer.validated_data['room_link']
            room_id = room_data['room_id']
            building_id = room_data['building_id']
            equipment_data = serializer.validated_data.get('equipment_data')

            if equipment_data:
                # Прямое создание оборудования
                equipment_data['room'] = room_data['room']
                equipment_serializer = EquipmentSerializer(data=equipment_data, context={'request': request})
                if equipment_serializer.is_valid():
                    equipment = equipment_serializer.save(author=request.user)
                    try:
                        UserAction.objects.create(
                            user=request.user,
                            action_type='CREATE_EQUIPMENT',
                            description=f"Создано оборудование: {equipment.name}",
                            content_object=equipment,
                            details={'name': equipment.name, 'id': equipment.id}
                        )
                    except Exception as e:
                        print(f"Error creating user action: {e}")
                    return Response(equipment_serializer.data, status=201)
                return Response(equipment_serializer.errors, status=400)

            # Возврат данных для формы
            return Response({
                'room_id': room_id,
                'building_id': building_id,
                'create_url': request.build_absolute_uri(
                    f"{reverse('equipment-list')}?room={room_id}&building={building_id}"
                ),
                'form_fields': {
                    'room': room_id,
                    'building': building_id,
                    'equipment_types': list(EquipmentType.objects.values('id', 'name')),
                    'status_choices': Equipment.STATUS_CHOICES
                }
            })
        return Response(serializer.errors, status=400)

class EquipmentTypeViewSet(viewsets.ModelViewSet):
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']
    filterset_fields = ['name']


class ContractDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = ContractDocumentSerializer
    pagination_class = ContractPagination
    permission_classes = [IsAuthenticated, IsAdminOrOwner]  # Добавляем кастомное разрешение
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['number']
    filterset_fields = ['created_at', 'valid_until']
    ordering_fields = ['created_at', 'number', 'valid_until']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = ContractDocument.objects.all().select_related('author')
        if self.request.user.is_authenticated:
            # Администраторы видят все контракты
            if self.request.user.is_staff or self.request.user.is_superuser:
                return queryset
            # Обычные пользователи видят только свои
            queryset = queryset.filter(author=self.request.user)
        return queryset

    def get_serializer_context(self):
        return {'request': self.request}

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Equipment.objects.filter(author=self.request.user)




    def perform_create(self, serializer):
        equipment = serializer.save(author=self.request.user)
        # Логируем создание одного оборудования
        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_EQUIPMENT',
                description=f"Создано оборудование: {equipment.name}",
                content_object=equipment,
                details={'name': equipment.name, 'id': equipment.id}
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

    def perform_update(self, serializer):
        instance = serializer.instance
        # Сохраняем старые значения для логирования
        old_data = EquipmentSerializer(instance, context={'request': self.request}).data # Сериализуем до сохранения

        updated_instance = serializer.save()

        # Собираем изменения
        changes = {}
        new_data = EquipmentSerializer(updated_instance, context={'request': self.request}).data
        for key, new_val in new_data.items():
            old_val = old_data.get(key)
            if old_val != new_val:
                changes[key] = {'old': old_val, 'new': new_val}

        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='UPDATE_EQUIPMENT',
                description=f"Обновлено оборудование: {updated_instance.name}",
                content_object=updated_instance,
                old_value=str(old_data) if changes else None,
                new_value=str(new_data) if changes else None,
                details={
                    'name': updated_instance.name,
                    'id': updated_instance.id,
                    'changes': changes
                }
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

    def perform_destroy(self, instance):
        # Сохраняем данные удаляемого объекта для логирования
        deleted_data = EquipmentSerializer(instance, context={'request': self.request}).data
        equipment_name = instance.name
        equipment_id = instance.id

        instance.delete()

        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='DELETE_EQUIPMENT',
                description=f"Удалено оборудование: {equipment_name}",
                details={
                    'name': equipment_name,
                    'id': equipment_id,
                    'deleted_data': deleted_data
                }
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

    @action(detail=False, methods=['post'], url_path='scan-qr')
    def scan_qr(self, request):
        serializer = QRScanSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # validated_data теперь выглядит как:
        # {
        #     'type': 'room' или 'equipment',
        #     'data': { ... },
        #     'equipments': [ ... ]  <- только если тип room
        # }

        return Response(serializer.validated_data)


    @action(detail=False, methods=['post'], url_path='bulk-create')
    @transaction.atomic
    def bulk_create(self, request):
        print("Received request data:", request.data)
        print("Request context:", {'request': request})
        serializer = BulkEquipmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            equipments = serializer.create(serializer.validated_data)
            print("Created equipments:", equipments)

            name_prefix = serializer.validated_data.get('name_prefix', '[без префикса]')

            # Логируем действие
            # Логируем действие для каждого созданного оборудования
            for equipment_item in equipments:
                try:
                    UserAction.objects.create(
                        user=request.user,
                        action_type='CREATE_EQUIPMENT',
                        description=f"Массово создано оборудование: {equipment_item.name}",
                        content_object=equipment_item,
                        details={
                            'name': equipment_item.name,
                            'id': equipment_item.id,
                            'bulk_prefix': name_prefix,
                            'total_created': len(equipments)
                        }
                    )
                except Exception as e:
                    print(f"Error creating user action: {e}")
            # Передаём контекст в EquipmentSerializer
            equipment_serializer = EquipmentSerializer(equipments, many=True, context={'request': request})
            return Response(equipment_serializer.data, status=201)
        print("Validation errors:", serializer.errors)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'], url_path='bulk-update-inn')
    @transaction.atomic
    def bulk_update_inn(self, request):
        serializer = BulkEquipmentInnUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            updated_equipments = serializer.update(None, serializer.validated_data)
            updated_ids = [equip.id for equip in updated_equipments]
            return Response({"updated_ids": updated_ids}, status=200)
        return Response(serializer.errors, status=400)


    @action(detail=False, methods=['post'], url_path='generate-qr-pdf')
    def generate_qr_pdf(self, request):
        # Получаем список ID оборудования из запроса
        equipment_ids = request.data.get('equipment_ids', [])
        if not equipment_ids:
            return Response({"error": "Не указаны ID оборудования"}, status=400)

        # Фильтруем оборудование по ID и текущему пользователю
        equipments = Equipment.objects.filter(id__in=equipment_ids, author=self.request.user)
        if not equipments.exists():
            return Response({"error": "Оборудование не найдено"}, status=404)

        # Создаём PDF в памяти
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        pdf.setFont("Helvetica", 12)

        # Начальные координаты для QR-кодов
        x, y = 50, height - 50
        qr_size = 100  # Размер QR-кода в пикселях
        spacing = 20  # Расстояние между QR-кодами

        qr_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')

        for equipment in equipments:
            # Получаем путь к существующему QR-коду
            qr_filename = f"equipment_qr_{equipment.uid}.png"
            qr_path = os.path.join(qr_dir, qr_filename)
            if not os.path.exists(qr_path):
                return Response({"error": f"QR-код для {equipment.name} не найден: {qr_path}"}, status=404)

            # Добавляем QR-код в PDF
            if y < 100:  # Если места на странице не хватает, создаём новую
                pdf.showPage()
                y = height - 50

            pdf.drawImage(qr_path, x, y - qr_size, width=qr_size, height=qr_size)
            pdf.drawString(x, y - qr_size - 15, f"{equipment.name} (ИНН: {equipment.inn})")
            y -= qr_size + spacing + 15  # Смещаем вниз для следующего QR-кода

        # Завершаем PDF
        pdf.showPage()
        pdf.save()

        # Получаем содержимое PDF
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()

        # Возвращаем PDF
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="equipment_qr_codes.pdf"'
        return response

    # @action(detail=False, methods=['post'], url_path='bulk-update-inn')
    # @transaction.atomic
    # def bulk_update_inn(self, request):
    #     serializer = BulkEquipmentInnUpdateSerializer(data=request.data, context={'request': request})
    #     if serializer.is_valid():
    #         equipments = serializer.update(serializer.validated_data) or []
    #         count = len(equipments) if equipments else 0
    #         UserAction.objects.create(
    #             user=request.user,
    #             action_type='UPDATE_INN',
    #             description=f"Обновлены ИНН для {count} оборудования"
    #         )
    #         return Response({
    #             "message": f"ИНН успешно обновлены для {count} оборудования",
    #             "equipments": EquipmentSerializer(equipments, many=True).data
    #         }, status=200)
    #     return Response(serializer.errors, status=400)


    @action(detail=False, methods=['delete'], url_path='bulk-delete')
    def bulk_delete_equipment(self, request):
        # Получаем список ID из тела запроса
        try:
            ids = request.data.get('ids', [])
            if not isinstance(ids, list):
                return Response({"error": "Идентификаторы должны быть в виде списка"}, status=status.HTTP_400_BAD_REQUEST)
            if not ids:
                return Response({"error": "Никаких удостоверений личности не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Недопустимый формат данных"}, status=status.HTTP_400_BAD_REQUEST)

        # Фильтруем объекты, принадлежавшие текущему пользователю
        equipments = Equipment.objects.filter(author=self.request.user, id__in=ids)

        if not equipments.exists():
            return Response({"error": "Оборудования не найдено или нет доступа"}, status=status.HTTP_404_NOT_FOUND)

        # Сохраняем данные перед удалением для логирования
        equipments_data_before_delete = list(equipments.values('id', 'name')) # Получаем id и name

        deleted_count, _ = equipments.delete() # equipments.delete() возвращает кортеж (кол-во, словарь по типам)

        for item_data in equipments_data_before_delete:
            try:
                UserAction.objects.create(
                    user=self.request.user,
                    action_type='DELETE_EQUIPMENT',
                    description=f"Массово удалено оборудование: {item_data['name']} (ID: {item_data['id']})",
                    details={
                        'name': item_data['name'],
                        'id': item_data['id'],
                        'bulk_delete_count_for_this_item': 1
                    }
                )
            except Exception as e:
                print(f"Error creating user action: {e}")

        if deleted_count > 0:
            try:
                UserAction.objects.create(
                    user=self.request.user,
                    action_type='DELETE_EQUIPMENT',
                    description=f"Массово удалено {deleted_count} ед. оборудования.",
                    details={
                        'deleted_count': deleted_count,
                        'deleted_ids': [item['id'] for item in equipments_data_before_delete]
                    }
                )
            except Exception as e:
                print(f"Error creating user action: {e}")

        return Response({"message": f"Успешно удалено {deleted_count} единиц оборудования"}, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='move-equipment')
    @transaction.atomic
    def move_equipment(self, request):
        serializer = MoveEquipmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            equipment_ids = serializer.validated_data.get('equipment_ids', [])
            from_room = serializer.validated_data.get('from_room_id')
            to_room = serializer.validated_data.get('to_room_id')

            if not from_room or not to_room:
                return Response({'detail': 'Неверные данные комнат.'}, status=400)

            equipments = Equipment.objects.filter(id__in=equipment_ids, room=from_room, author=self.request.user)
            for equipment in equipments:
                MovementHistory.objects.create(
                    equipment=equipment,
                    from_room=from_room,
                    to_room=to_room
                )
                equipment.room = to_room
                equipment.save()

            for equipment_item in equipments:
                try:
                    UserAction.objects.create(
                        user=request.user,
                        action_type='MOVE',
                        description=f"Оборудование '{equipment_item.name}' перемещено из каб. {from_room.number} в каб. {to_room.number}",
                        content_object=equipment_item,
                        details={
                            'name': equipment_item.name,
                            'equipment_id': equipment_item.id,
                            'from_room_id': from_room.id,
                            'from_room_number': from_room.number,
                            'to_room_id': to_room.id,
                            'to_room_number': to_room.number,
                            'count': 1
                        }
                    )
                except Exception as e:
                    print(f"Error creating user action: {e}")
            if equipments.count() > 1:
                try:
                    UserAction.objects.create(
                        user=request.user,
                        action_type='MOVE',
                        description=f"Массово перемещено {equipments.count()} ед. оборудования из каб. {from_room.number} в каб. {to_room.number}",
                        details={
                            'count': equipments.count(),
                            'from_room_id': from_room.id,
                            'from_room_number': from_room.number,
                            'to_room_id': to_room.id,
                            'to_room_number': to_room.number,
                            'equipment_ids': [eq.id for eq in equipments]
                        }
                    )
                except Exception as e:
                    print(f"Error creating user action: {e}")
            return Response({'message': f'Оборудование перемещено из кабинета {from_room.number} в кабинет {to_room.number}'})
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], url_path=r'rooms-by-building/(?P<building_id>\d+)')
    def rooms_by_building(self, request, building_id=None):
        rooms = Room.objects.filter(building_id=building_id)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path=r'equipment-by-room/(?P<room_id>\d+)')
    def equipment_by_room(self, request, room_id=None):
        try:
            print(f"📦 Получение оборудования для комнаты: {room_id}")

            equipments = Equipment.objects.filter(room_id=room_id, author=request.user)
            print(f"🔍 Найдено {equipments.count()} единиц техники")

            if not equipments.exists():
                raise NotFound("Оборудование не найдено или недоступно")

            serializer = EquipmentSerializer(equipments, many=True, context={'request': request})
            return Response(serializer.data)

        except Exception as e:
            print(f"🔥 Ошибка при получении оборудования: {e}")
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'], url_path='my-equipments')
    def my_equipments(self, request):
        equipments = self.get_queryset()
        serializer = self.get_serializer(equipments, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['get'], url_path='my-actions')
    def my_actions(self, request):
        actions = UserAction.objects.filter(user=request.user)[:10]  # Последние 10 действий
        serializer = UserActionSerializer(actions, many=True)
        return Response(serializer.data)






    @action(detail=False, methods=['get'], url_path='filter')
    def equipment_filter(self, request):
        building_id = request.query_params.get('building_id')
        floor_id = request.query_params.get('floor_id')
        room_id = request.query_params.get('room_id')
        type_id = request.query_params.get('type_id')
        status = request.query_params.get('status')

        equipments = Equipment.objects.filter(author=self.request.user)

        if building_id:
            equipments = equipments.filter(room__floor__building_id=building_id)
        if floor_id:
            equipments = equipments.filter(room__floor_id=floor_id)
        if room_id:
            equipments = equipments.filter(room_id=room_id)
        if type_id:
            equipments = equipments.filter(type_id=type_id)
        if status:
            equipments = equipments.filter(status=status)

        page = self.paginate_queryset(equipments)
        if page is not None:
            serializer = CustomEquipmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CustomEquipmentSerializer(equipments, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['get'], url_path=r'by-room/(?P<room_id>\d+)/data')
    def equipment_by_type(self, request, room_id=None):
        # Проверяем существование комнаты
        room = get_object_or_404(Room, id=room_id)

        # Маппинг имён типов
        TYPE_NAME_MAPPING = {
            'компьютер': 'kompyters',
            'ноутбук': 'laptops',
            'моноблок': 'monoblocks',
            'принтер': 'printers',
            'удлинитель': 'extension_cords',
            'электронная доска': 'interactive_boards',
            'проектор': 'projectors',
            'тв': 'tvs',
            'роутер': 'routers'
        }

        # Получаем оборудование пользователя в комнате
        equipments = Equipment.objects.filter(
            room_id=room_id,
            author=self.request.user
        ).select_related('type')

        # Группируем по типам
        grouped_data = defaultdict(list)
        for equipment in equipments:
            type_name = equipment.type.name.lower()
            key = TYPE_NAME_MAPPING.get(type_name, type_name)
            serializer = EquipmentSerializer(equipment)
            grouped_data[key].append(serializer.data)

        # Преобразуем в нужный формат: [ { "name": ..., "items": [...] }, ... ]
        result = [
            {
                "name": key,
                "items": value
            } for key, value in grouped_data.items() if value
        ]

        # Если ничего не найдено
        if not result:
            return Response([], status=status.HTTP_200_OK)

        return Response(result)


class ComputerSpecificationViewSet(ModelViewSet):
   serializer_class = ComputerSpecificationSerializer
   permission_classes = [IsAuthenticated]

   def get_queryset(self):
       return ComputerSpecification.objects.filter(author=self.request.user)

   def perform_create(self, serializer):
       serializer.save(author=self.request.user)



class ComputerDetailsViewSet(viewsets.ModelViewSet):
    queryset = ComputerDetails.objects.all()
    serializer_class = ComputerDetailsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['has_keyboard', 'has_mouse']


class MovementHistoryViewSet(viewsets.ModelViewSet):
    queryset = MovementHistory.objects.all()
    serializer_class = MovementHistorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['equipment__name']
    filterset_fields = ['equipment', 'from_room', 'to_room', 'moved_at']

    def perform_create(self, serializer):
        movement = serializer.save()
        if movement.to_room:
            movement.equipment.room = movement.to_room
            movement.equipment.save()



class PrinterCharViewSet(viewsets.ModelViewSet):
    queryset = PrinterChar.objects.all()
    serializer_class = PrinterCharSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'model']
    search_fields = ['name', 'model']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PrinterChar.objects.filter(author=self.request.user)
    def perform_create(self, serializer):
        printer = serializer.save(author=self.request.user)
        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_EQUIPMENT',
                description=f"Создана характеристика принтера: {str(printer)}",
                content_object=printer,
                details={'name': str(printer), 'id': printer.id, 'model_type': 'PrinterChar'}
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

class ExtenderCharViewSet(viewsets.ModelViewSet):
    queryset = ExtenderChar.objects.all()
    serializer_class = ExtenderCharSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'model']
    search_fields = ['name', 'model']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ExtenderChar.objects.filter(author=self.request.user)
    def perform_create(self, serializer):
        extender = serializer.save(author=self.request.user)
        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_EQUIPMENT',
                description=f"Создана характеристика удлинителя: {str(extender)}",
                content_object=extender,
                details={'name': str(extender), 'id': extender.id, 'model_type': 'ExtenderChar'}
            )
        except Exception as e:
            print(f"Error creating user action: {e}")
            
class TVCharViewSet(viewsets.ModelViewSet):
    queryset = TVChar.objects.all()
    serializer_class = TVCharSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'model']
    search_fields = ['name', 'model']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return TVChar.objects.filter(author=self.request.user)
    def perform_create(self, serializer):
        tv = serializer.save(author=self.request.user)
        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_EQUIPMENT',
                description=f"Создана характеристика телевизора: {str(tv)}",
                content_object=tv,
                details={'name': str(tv), 'id': tv.id, 'model_type': 'TVChar'}
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

class RouterCharViewSet(viewsets.ModelViewSet):
    queryset = RouterChar.objects.all()
    serializer_class = RouterCharSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'model']
    search_fields = ['name', 'model']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return RouterChar.objects.filter(author=self.request.user)
    def perform_create(self, serializer):
        router = serializer.save(author=self.request.user)
        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_EQUIPMENT',
                description=f"Создана характеристика роутера: {str(router)}",
                content_object=router,
                details={'name': str(router), 'id': router.id, 'model_type': 'RouterChar'}
            )
        except Exception as e:
            print(f"Error creating user action: {e}")


# ViewSet для спецификаций
class PrinterSpecificationViewSet(ModelViewSet):
    serializer_class = PrinterSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrinterSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class ExtenderSpecificationViewSet(ModelViewSet):
    serializer_class = ExtenderSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExtenderSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class RouterSpecificationViewSet(ModelViewSet):
    serializer_class = RouterSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RouterSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class TVSpecificationViewSet(ModelViewSet):
    serializer_class = TVSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TVSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

######################################################################
class ProjectorCharViewSet(ModelViewSet):
    serializer_class = ProjectorCharSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectorChar.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class ProjectorSpecificationViewSet(ModelViewSet):
    serializer_class = ProjectorSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectorSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class WhiteboardCharViewSet(ModelViewSet):
    serializer_class = WhiteboardCharSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WhiteboardChar.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class WhiteboardSpecificationViewSet(ModelViewSet):
    serializer_class = WhiteboardSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WhiteboardSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NotebookCharViewSet(ModelViewSet):
    serializer_class = NotebookCharSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotebookChar.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class NotebookSpecificationViewSet(ModelViewSet):
    serializer_class = NotebookSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotebookSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class MonoblokCharViewSet(ModelViewSet):
    serializer_class = MonoblokCharSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MonoblokChar.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class MonoblokSpecificationViewSet(ModelViewSet):
    serializer_class = MonoblokSpecificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MonoblokSpecification.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class QRScanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QRScanSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            object_type = serializer.validated_data['object_type']
            obj_data = serializer.validated_data['object']
            # Определение content_object для QRScanView
            scanned_object = None
            if object_type == 'room' and 'id' in obj_data:
                try:
                    scanned_object = Room.objects.get(id=obj_data['id'])
                except Room.DoesNotExist:
                    pass
            elif object_type == 'equipment' and 'id' in obj_data:
                try:
                    scanned_object = Equipment.objects.get(id=obj_data['id'])
                except Equipment.DoesNotExist:
                    pass

            try:
                UserAction.objects.create(
                    user=request.user,
                    action_type='SCAN',
                    description=f"Отсканирован QR-код: {object_type} - ID: {obj_data.get('id', 'N/A')}",
                    content_object=scanned_object,
                    details={'type': object_type, 'data': obj_data}
                )
            except Exception as e:
                print(f"Error creating user action: {e}")
            return Response({
                'type': object_type,
                'data': obj_data
            })
        return Response(serializer.errors, status=400)




class RepairViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления записями о ремонте.
    """
    serializer_class = RepairSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Фильтр записей ремонта по оборудованию текущего пользователя.
        """
        return Repair.objects.filter(equipment__author=self.request.user).select_related('equipment')

    def perform_create(self, serializer):
        repair = serializer.save()
        equipment = repair.equipment
        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_REPAIR',
                description=f"Создана запись о ремонте для оборудования: {equipment.name}",
                content_object=repair,
                details={
                    'equipment_id': equipment.id,
                    'name': equipment.name,
                    'repair_id': repair.id,
                    'status': repair.status,
                    'notes': repair.notes
                }
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

    def perform_update(self, serializer):
        instance = serializer.instance
        old_status = instance.status
        old_notes = instance.notes

        repair = serializer.save()
        equipment = repair.equipment

        changes = {}
        if old_status != repair.status:
            changes['status'] = {'old': old_status, 'new': repair.status}
        if old_notes != repair.notes:
            changes['notes'] = {'old': old_notes, 'new': repair.notes}

        if changes:
            try:
                UserAction.objects.create(
                    user=self.request.user,
                    action_type='UPDATE_REPAIR',
                    description=f"Обновлена запись о ремонте для оборудования: {equipment.name}",
                    content_object=repair,
                    old_value=f"Status: {old_status}, Notes: {old_notes}",
                    new_value=f"Status: {repair.status}, Notes: {repair.notes}",
                    details={
                        'equipment_id': equipment.id,
                        'name': equipment.name,
                        'repair_id': repair.id,
                        'changes': changes
                    }
                )
            except Exception as e:
                print(f"Error creating user action: {e}")

    @action(detail=True, methods=['post'], url_path='complete')
    @transaction.atomic
    def complete_repair(self, request, pk=None):
        """
        Завершение ремонта оборудования (успешное).
        """
        repair = self.get_object()

        # Проверяем, что ремонт еще не завершен
        if repair.status != 'IN_PROGRESS':
            return Response(
                {"detail": "Этот ремонт уже завершен."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем запись о ремонте
        repair.status = 'COMPLETED'
        if request.data.get('notes'):
            repair.notes += f"\n\n{request.data.get('notes')}"
        repair.save()

        # Обновленные данные будут получены через сохранение модели
        return Response({
            "detail": "Ремонт успешно завершен.",
            "repair": RepairSerializer(repair).data,
            "equipment": EquipmentSerializer(repair.equipment).data
        })

    @action(detail=True, methods=['post'], url_path='fail')
    @transaction.atomic
    def fail_repair(self, request, pk=None):
        """
        Завершение ремонта оборудования с отрицательным результатом.
        """
        repair = self.get_object()

        # Проверяем, что ремонт еще не завершен
        if repair.status != 'IN_PROGRESS':
            return Response(
                {"detail": "Этот ремонт уже завершен."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем запись о ремонте
        repair.status = 'FAILED'
        if request.data.get('notes'):
            repair.notes += f"\n\n{request.data.get('notes')}"
        repair.save()

        # Обновленные данные будут получены через сохранение модели
        return Response({
            "detail": "Ремонт завершен с отрицательным результатом. Оборудование отмечено для утилизации.",
            "repair": RepairSerializer(repair).data,
            "equipment": EquipmentSerializer(repair.equipment).data
        })


class DisposalViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления записями об утилизации.
    """
    serializer_class = DisposalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Фильтр записей утилизации по оборудованию текущего пользователя.
        """
        return Disposal.objects.filter(equipment__author=self.request.user).select_related('equipment')

    def perform_create(self, serializer):
        disposal = serializer.save()
        equipment = disposal.equipment
        try:
            UserAction.objects.create(
                user=self.request.user,
                action_type='CREATE_DISPOSAL',
                description=f"Создана запись об утилизации для оборудования: {equipment.name}",
                content_object=disposal,
                details={
                    'equipment_id': equipment.id,
                    'name': equipment.name,
                    'disposal_id': disposal.id,
                    'reason': disposal.reason,
                    'notes': disposal.notes
                }
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

    def perform_update(self, serializer):
        instance = serializer.instance
        old_reason = instance.reason
        old_notes = instance.notes

        disposal = serializer.save()
        equipment = disposal.equipment

        changes = {}
        if old_reason != disposal.reason:
            changes['reason'] = {'old': old_reason, 'new': disposal.reason}
        if old_notes != disposal.notes:
            changes['notes'] = {'old': old_notes, 'new': disposal.notes}

        if changes:
            try:
                UserAction.objects.create(
                    user=self.request.user,
                    action_type='UPDATE_DISPOSAL',
                    description=f"Обновлена запись об утилизации для оборудования: {equipment.name}",
                    content_object=disposal,
                    old_value=f"Reason: {old_reason}, Notes: {old_notes}",
                    new_value=f"Reason: {disposal.reason}, Notes: {disposal.notes}",
                    details={
                        'equipment_id': equipment.id,
                        'name': equipment.name,
                        'disposal_id': disposal.id,
                        'changes': changes
                    }
                )
            except Exception as e:
                print(f"Error creating user action: {e}")


class EquipmentMaintenanceViewSet(viewsets.ViewSet):
    """
    ViewSet для удобного управления обслуживанием оборудования.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='send-to-repair')
    @transaction.atomic
    def send_to_repair(self, request, pk=None):
        """
        Отправить оборудование на ремонт.
        """
        # Получаем оборудование
        equipment = get_object_or_404(Equipment, pk=pk, author=request.user)

        # Проверяем текущий статус
        if equipment.status == 'DISPOSED':
            return Response(
                {"detail": "Нельзя отправить на ремонт утилизированное оборудование."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if equipment.status == 'NEEDS_REPAIR':
            return Response(
                {"detail": "Оборудование уже находится в ремонте."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if hasattr(equipment, 'repair_record'):
            return Response(
                {"detail": "Для этого оборудования уже существует запись о ремонте."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем данные для записи о ремонте
        repair_data = {
            'equipment': equipment.id,
            'notes': request.data.get('notes', 'Запись создана через API')
        }

        # Создаем запись о ремонте
        serializer = RepairSerializer(data=repair_data)
        serializer.is_valid(raise_exception=True)
        repair = serializer.save() # serializer.save() вызовет perform_create из RepairViewSet, где логирование уже есть
        # Дополнительное логирование для действия "отправить на ремонт"
        equipment = repair.equipment
        try:
            UserAction.objects.create(
                user=request.user,
                action_type='SEND_TO_REPAIR',
                description=f"Оборудование '{equipment.name}' отправлено на ремонт.",
                content_object=equipment,
                details={
                    'equipment_id': equipment.id,
                    'name': equipment.name,
                    'repair_id': repair.id,
                    'notes': request.data.get('notes', 'Запись создана через API')
                }
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

        return Response({
            "detail": "Оборудование успешно отправлено на ремонт.",
            "repair": RepairSerializer(repair).data,
            "equipment": EquipmentSerializer(equipment).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='dispose')
    @transaction.atomic
    def dispose_equipment(self, request, pk=None):
        """
        Утилизировать оборудование.
        """
        # Получаем оборудование
        equipment = get_object_or_404(Equipment, pk=pk, author=request.user)

        # Проверяем текущий статус
        if equipment.status == 'DISPOSED':
            return Response(
                {"detail": "Оборудование уже отмечено как утилизированное."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if hasattr(equipment, 'disposal_record'):
            return Response(
                {"detail": "Для этого оборудования уже существует запись об утилизации."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, что указана причина утилизации
        reason = request.data.get('reason')
        if not reason:
            return Response(
                {"detail": "Необходимо указать причину утилизации."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем данные для записи об утилизации
        disposal_data = {
            'equipment': equipment.id,
            'reason': reason,
            'notes': request.data.get('notes', '')
        }

        # Создаем запись об утилизации
        serializer = DisposalSerializer(data=disposal_data)
        serializer.is_valid(raise_exception=True)
        disposal = serializer.save() # serializer.save() вызовет perform_create из DisposalViewSet
        # Дополнительное логирование для действия "утилизировать"
        equipment = disposal.equipment
        try:
            UserAction.objects.create(
                user=request.user,
                action_type='DISPOSE_EQUIPMENT',
                description=f"Оборудование '{equipment.name}' отправлено на утилизацию.",
                content_object=equipment,
                details={
                    'equipment_id': equipment.id,
                    'name': equipment.name,
                    'disposal_id': disposal.id,
                    'reason': request.data.get('reason'),
                    'notes': request.data.get('notes', '')
                }
            )
        except Exception as e:
            print(f"Error creating user action: {e}")

        return Response({
            "detail": "Оборудование успешно отмечено как утилизированное.",
            "disposal": DisposalSerializer(disposal).data,
            "equipment": EquipmentSerializer(equipment).data
        }, status=status.HTTP_201_CREATED)