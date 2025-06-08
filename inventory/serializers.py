from rest_framework import serializers
from .models import (EquipmentType, Equipment, ComputerDetails,
                     MovementHistory, ContractDocument, ComputerSpecification,
                     RouterSpecification, ExtenderSpecification, TVSpecification, PrinterSpecification,
                     RouterChar, ExtenderChar, TVChar, PrinterChar,
                     NotebookChar, NotebookSpecification, MonoblokChar, MonoblokSpecification,
                     ProjectorChar, ProjectorSpecification, WhiteboardChar, WhiteboardSpecification,
                     Repair, Disposal, Disk, DiskSpecification, MonitorChar, MonitorSpecification,
                     GPU, GPUSpecification
                     )
from datetime import datetime
from university.models import Room
from university.serializers import RoomSerializer
from user.serializers import UserSerializer
import json
from io import BytesIO
import qrcode
from django.core.files import File
from django.contrib.auth import get_user_model

User = get_user_model()

class EquipmentNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'name']

class EquipmentTypeSerializer(serializers.ModelSerializer):
    requires_computer_details = serializers.SerializerMethodField()

    def get_requires_computer_details(self, obj):
        # Считаем, что только тип с name="Компьютер" требует характеристики
        computer_types = ['компьютер', 'ноутбук', 'моноблок']
        return obj.name.lower() in computer_types

    class Meta:
        model = EquipmentType
        fields = ['id', 'name', 'requires_computer_details']
        read_only_fields = ['id']

class RepairSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repair
        fields = ['id', 'start_date', 'end_date', 'status', 'notes']

class DisposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disposal
        fields = ['id', 'equipment', 'disposal_date', 'reason', 'notes']
        read_only_fields = ['equipment', 'disposal_date']


class ContractDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None

    def validate_number(self, value):
        if not value or value.strip() == "":
            raise serializers.ValidationError("Номер договора обязателен для заполнения.")
        return value

    def validate(self, data):
        created_at = data.get('created_at')
        valid_until = data.get('valid_until')

        if valid_until and created_at and valid_until <= created_at:
            raise serializers.ValidationError({
                "valid_until": "Дата окончания должна быть позже даты создания."
            })

        if valid_until and valid_until < datetime.now().date():
            raise serializers.ValidationError({
                "valid_until": "Дата окончания не может быть раньше текущей даты."
            })

        return data

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

    class Meta:
        model = ContractDocument
        fields = ['id', 'number', 'file', 'file_url', 'created_at', 'valid_until', 'author']
        read_only_fields = ['id', 'file_url', 'created_at', 'author']


class ComputerDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComputerDetails
        fields = [
            'cpu',
            'ram',
            'has_keyboard',
            'has_mouse'
        ]


class GPUSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPUSpecification
        exclude = ('computer_specification', 'notebook_specification', 'monoblok_specification')


class GPUSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPU
        fields = '__all__'



class DiskSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiskSpecification
        exclude = ('computer_specification', 'notebook_specification', 'monoblok_specification')

class DiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disk
        fields = '__all__'

class ComputerSpecificationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    disk_specifications = DiskSpecificationSerializer(many=True, required=False)
    gpu_specifications = GPUSpecificationSerializer(many=True, required=False)  # ДОБАВЛЕНО

    class Meta:
        model = ComputerSpecification
        fields = [
            'id', 'cpu', 'ram', 'has_keyboard', 'has_mouse',
            'monitor_size', 'created_at', 'uid', 'author', 'author_id', 
            'disk_specifications', 'gpu_specifications'  # ДОБАВЛЕНО
        ]
        read_only_fields = ['created_at', 'uid', 'author']

    def create(self, validated_data):
        disks_data = validated_data.pop('disk_specifications', [])
        gpus_data = validated_data.pop('gpu_specifications', [])  # ДОБАВЛЕНО
        specification = ComputerSpecification.objects.create(**validated_data)
        
        for disk_data in disks_data:
            DiskSpecification.objects.create(computer_specification=specification, **disk_data)
        
        for gpu_data in gpus_data:  # ДОБАВЛЕНО
            GPUSpecification.objects.create(computer_specification=specification, **gpu_data)
            
        return specification

    def update(self, instance, validated_data):
        disks_data = validated_data.pop('disk_specifications', None)
        gpus_data = validated_data.pop('gpu_specifications', None)  # ДОБАВЛЕНО

        # Update specification instance
        instance.cpu = validated_data.get('cpu', instance.cpu)
        instance.ram = validated_data.get('ram', instance.ram)
        instance.has_keyboard = validated_data.get('has_keyboard', instance.has_keyboard)
        instance.has_mouse = validated_data.get('has_mouse', instance.has_mouse)
        instance.monitor_size = validated_data.get('monitor_size', instance.monitor_size)
        instance.save()

        if disks_data is not None:
            instance.disk_specifications.all().delete()
            for disk_data in disks_data:
                DiskSpecification.objects.create(computer_specification=instance, **disk_data)

        if gpus_data is not None:  # ДОБАВЛЕНО
            instance.gpu_specifications.all().delete()
            for gpu_data in gpus_data:
                GPUSpecification.objects.create(computer_specification=instance, **gpu_data)

        return instance
    


class PrinterCharSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrinterChar
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'equipment')



class ExtenderCharSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtenderChar
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'equipment')


class RouterCharSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouterChar
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'equipment')


class TVCharSerializer(serializers.ModelSerializer):
    class Meta:
        model = TVChar
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'equipment')


class PrinterSpecificationSerializer(serializers.ModelSerializer):
    def get_queryset(self):
        user = self.context['request'].user
        if user.is_authenticated:
            return PrinterSpecification.objects.filter(author=user)
        return PrinterSpecification.objects.none()

    class Meta:
        model = PrinterSpecification
        fields = ['id', 'model', 'color', 'duplex', 'author', 'created_at', 'updated_at']

class ExtenderSpecificationSerializer(serializers.ModelSerializer):
    length = serializers.FloatField()

    def get_queryset(self):
        user = self.context['request'].user
        if user.is_authenticated:
            return ExtenderSpecification.objects.filter(author=user)
        return ExtenderSpecification.objects.none()

    class Meta:
        model = ExtenderSpecification
        fields = ['id', 'ports', 'length', 'author', 'created_at', 'updated_at']

class RouterSpecificationSerializer(serializers.ModelSerializer):
    WIFI_STANDARDS = [
        ('802.11n', 'Wi-Fi 4'),
        ('802.11ac', 'Wi-Fi 5'),
        ('802.11ax', 'Wi-Fi 6'),
    ]
    wifi_standart = serializers.ChoiceField(choices=WIFI_STANDARDS)

    def get_queryset(self):
        user = self.context['request'].user
        if user.is_authenticated:
            return RouterSpecification.objects.filter(author=user)
        return RouterSpecification.objects.none()

    class Meta:
        model = RouterSpecification
        fields = ['id', 'model', 'ports', 'wifi_standart', 'author', 'created_at', 'updated_at']

class TVSpecificationSerializer(serializers.ModelSerializer):
    screen_size = serializers.IntegerField()

    def get_queryset(self):
        user = self.context['request'].user
        if user.is_authenticated:
            return TVSpecification.objects.filter(author=user)
        return TVSpecification.objects.none()

    class Meta:
        model = TVSpecification
        fields = ['id', 'model', 'screen_size', 'author', 'created_at', 'updated_at']



#############################################
class NotebookCharSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = NotebookChar
        fields = ['id', 'cpu', 'ram', 'monitor_size', 'author', 'created_at']
        read_only_fields = ['equipment']

class NotebookSpecificationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    disk_specifications = DiskSpecificationSerializer(many=True, required=False)
    gpu_specifications = GPUSpecificationSerializer(many=True, required=False)  # ДОБАВЛЕНО

    class Meta:
        model = NotebookSpecification
        fields = ['id', 'cpu', 'ram', 'monitor_size', 'author', 'created_at', 
                 'disk_specifications', 'gpu_specifications']  # ДОБАВЛЕНО

    def create(self, validated_data):
        disks_data = validated_data.pop('disk_specifications', [])
        gpus_data = validated_data.pop('gpu_specifications', [])  # ДОБАВЛЕНО
        specification = NotebookSpecification.objects.create(**validated_data)
        
        for disk_data in disks_data:
            DiskSpecification.objects.create(notebook_specification=specification, **disk_data)
        
        for gpu_data in gpus_data:  # ДОБАВЛЕНО
            GPUSpecification.objects.create(notebook_specification=specification, **gpu_data)
            
        return specification

    def update(self, instance, validated_data):
        disks_data = validated_data.pop('disk_specifications', None)
        gpus_data = validated_data.pop('gpu_specifications', None)  # ДОБАВЛЕНО

        instance.cpu = validated_data.get('cpu', instance.cpu)
        instance.ram = validated_data.get('ram', instance.ram)
        instance.monitor_size = validated_data.get('monitor_size', instance.monitor_size)
        instance.save()

        if disks_data is not None:
            instance.disk_specifications.all().delete()
            for disk_data in disks_data:
                DiskSpecification.objects.create(notebook_specification=instance, **disk_data)

        if gpus_data is not None:  # ДОБАВЛЕНО
            instance.gpu_specifications.all().delete()
            for gpu_data in gpus_data:
                GPUSpecification.objects.create(notebook_specification=instance, **gpu_data)

        return instance

class MonoblokCharSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = MonoblokChar
        fields = ['id', 'cpu', 'ram', 'has_keyboard', 'has_mouse', 'monitor_size', 'author']
        read_only_fields = ['equipment']

class MonoblokSpecificationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    disk_specifications = DiskSpecificationSerializer(many=True, required=False)
    gpu_specifications = GPUSpecificationSerializer(many=True, required=False)  # ДОБАВЛЕНО

    class Meta:
        model = MonoblokSpecification
        fields = ['id', 'cpu', 'ram', 'has_keyboard', 'has_mouse', 'monitor_size', 
                 'author', 'created_at', 'disk_specifications', 'gpu_specifications']  # ДОБАВЛЕНО

    def create(self, validated_data):
        disks_data = validated_data.pop('disk_specifications', [])
        gpus_data = validated_data.pop('gpu_specifications', [])  # ДОБАВЛЕНО
        specification = MonoblokSpecification.objects.create(**validated_data)
        
        for disk_data in disks_data:
            DiskSpecification.objects.create(monoblok_specification=specification, **disk_data)
        
        for gpu_data in gpus_data:  # ДОБАВЛЕНО
            GPUSpecification.objects.create(monoblok_specification=specification, **gpu_data)
            
        return specification

    def update(self, instance, validated_data):
        disks_data = validated_data.pop('disk_specifications', None)
        gpus_data = validated_data.pop('gpu_specifications', None)  # ДОБАВЛЕНО

        instance.cpu = validated_data.get('cpu', instance.cpu)
        instance.ram = validated_data.get('ram', instance.ram)
        instance.has_keyboard = validated_data.get('has_keyboard', instance.has_keyboard)
        instance.has_mouse = validated_data.get('has_mouse', instance.has_mouse)
        instance.monitor_size = validated_data.get('monitor_size', instance.monitor_size)
        instance.save()

        if disks_data is not None:
            instance.disk_specifications.all().delete()
            for disk_data in disks_data:
                DiskSpecification.objects.create(monoblok_specification=instance, **disk_data)

        if gpus_data is not None:  # ДОБАВЛЕНО
            instance.gpu_specifications.all().delete()
            for gpu_data in gpus_data:
                GPUSpecification.objects.create(monoblok_specification=instance, **gpu_data)

        return instance


class ProjectorCharSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = ProjectorChar
        fields = ['id', 'model', 'lumens', 'resolution', 'throw_type', 'author', 'created_at', 'updated_at']
        read_only_fields = ['equipment']

class ProjectorSpecificationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = ProjectorSpecification
        fields = ['id', 'model', 'lumens', 'resolution', 'throw_type', 'author', 'created_at', 'updated_at']

class WhiteboardCharSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = WhiteboardChar
        fields = ['id', 'model', 'screen_size', 'touch_type',  'author', 'created_at', 'updated_at']
        read_only_fields = ['equipment']

class WhiteboardSpecificationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = WhiteboardSpecification
        fields = ['id', 'model', 'screen_size', 'touch_type', 'author', 'created_at', 'updated_at']


#######################################################

import re
class EquipmentFromLinkSerializer(serializers.Serializer):
    room_link = serializers.URLField(required=True)

    def validate_room_link(self, value):
        match = re.match(r'.*/rooms/(\d+)/\?building=(\d+)', value)
        if not match:
            raise serializers.ValidationError("Неверный формат ссылки")
        room_id, building_id = match.groups()
        try:
            room = Room.objects.get(id=room_id, building_id=building_id)
        except Room.DoesNotExist:
            raise serializers.ValidationError("Кабинет или корпус не найдены")
        return {'room_id': room_id, 'building_id': building_id, 'room': room}
    

class MonitorCharSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitorChar
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'equipment')


class MonitorSpecificationSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    def get_queryset(self):
        user = self.context['request'].user
        if user.is_authenticated:
            return MonitorSpecification.objects.filter(author=user)
        return MonitorSpecification.objects.none()

    class Meta:
        model = MonitorSpecification
        fields = ['id', 'model', 'serial_number', 'screen_size', 'resolution', 'panel_type', 'refresh_rate', 'author', 'created_at', 'updated_at']


class EquipmentSerializer(serializers.ModelSerializer):
    COMPUTER_TYPES = {'компьютер'}
    NOTEBOOK_TYPES = {'ноутбук'}
    MONOBLOK_TYPES = {'моноблок'}
    PRINTER_TYPES = {'принтер', 'мфу'}
    EXTENDER_TYPES = {'удлинитель', 'сетевой фильтр'}
    ROUTER_TYPES = {'роутер'}
    TV_TYPES = {'телевизор'}
    PROJECTOR_TYPES = {'проектор'}
    WHITEBOARD_TYPES = {'электронная доска'}
    MONITOR_TYPES = {'монитор'}  # Добавить

    # Существующие поля
    contract = ContractDocumentSerializer(read_only=True, allow_null=True)
    type = serializers.PrimaryKeyRelatedField(queryset=EquipmentType.objects.all())
    type_data = EquipmentTypeSerializer(source='type', read_only=True)
    room = serializers.PrimaryKeyRelatedField(queryset=Room.objects.all(), allow_null=True, required=False)
    room_data = RoomSerializer(source='room', read_only=True, allow_null=True)
    qr_code_url = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        source='author'
    )
    location = serializers.CharField(required=False, allow_null=True)
    repair_record = RepairSerializer(read_only=True)
    disposal_record = DisposalSerializer(read_only=True)

    disks = DiskSerializer(many=True, read_only=True)
    # Поля для характеристик
    computer_details = ComputerDetailsSerializer(required=False, allow_null=True)
    printer_char = PrinterCharSerializer(required=False, allow_null=True)
    extender_char = ExtenderCharSerializer(required=False, allow_null=True)
    router_char = RouterCharSerializer(required=False, allow_null=True)
    tv_char = TVCharSerializer(required=False, allow_null=True)
    notebook_char = NotebookCharSerializer(required=False, allow_null=True)
    monoblok_char = MonoblokCharSerializer(required=False, allow_null=True)
    projector_char = ProjectorCharSerializer(required=False, allow_null=True)
    whiteboard_char = WhiteboardCharSerializer(required=False, allow_null=True)
    monitor_char = MonitorCharSerializer(required=False, allow_null=True)  # Добавить


    # Поля для шаблонов
    computer_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=ComputerSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона компьютерной спецификации для автозаполнения характеристик"
    )
    printer_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=PrinterSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации принтера для автозаполнения характеристик"
    )
    extender_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=ExtenderSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации удлинителя для автозаполнения характеристик"
    )
    router_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=RouterSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации роутера для автозаполнения характеристик"
    )
    tv_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=TVSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации телевизора для автозаполнения характеристик"
    )
    notebook_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=NotebookSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации ноутбука для автозаполнения характеристик"
    )
    monoblok_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=MonoblokSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации моноблока для автозаполнения характеристик"
    )
    projector_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=ProjectorSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации проектора для автозаполнения характеристик"
    )
    whiteboard_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=WhiteboardSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации электронной доски для автозаполнения характеристик"
    )
    monitor_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=MonitorSpecification.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        help_text="ID шаблона спецификации монитора для автозаполнения характеристик"
    )
    

    # Поля для отображения данных спецификаций
    computer_specification_data = ComputerSpecificationSerializer(source='computer_details', read_only=True, allow_null=True)
    printer_specification_data = PrinterSpecificationSerializer(source='printer_char', read_only=True, allow_null=True)
    extender_specification_data = ExtenderSpecificationSerializer(source='extender_char', read_only=True, allow_null=True)
    router_specification_data = RouterSpecificationSerializer(source='router_char', read_only=True, allow_null=True)
    tv_specification_data = TVSpecificationSerializer(source='tv_char', read_only=True, allow_null=True)
    notebook_specification_data = NotebookSpecificationSerializer(source='notebook_char', read_only=True, allow_null=True)
    monoblok_specification_data = MonoblokSpecificationSerializer(source='monoblok_char', read_only=True, allow_null=True)
    projector_specification_data = ProjectorSpecificationSerializer(source='projector_char', read_only=True, allow_null=True)
    whiteboard_specification_data = WhiteboardSpecificationSerializer(source='whiteboard_char', read_only=True, allow_null=True)
    monitor_specification_data = MonitorSpecificationSerializer(source='monitor_char', read_only=True, allow_null=True)  # Добавить

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            self.fields['computer_specification_id'].queryset = ComputerSpecification.objects.filter(author=request.user)
            self.fields['printer_specification_id'].queryset = PrinterSpecification.objects.filter(author=request.user)
            self.fields['extender_specification_id'].queryset = ExtenderSpecification.objects.filter(author=request.user)
            self.fields['router_specification_id'].queryset = RouterSpecification.objects.filter(author=request.user)
            self.fields['tv_specification_id'].queryset = TVSpecification.objects.filter(author=request.user)
            self.fields['notebook_specification_id'].queryset = NotebookSpecification.objects.filter(author=request.user)
            self.fields['monoblok_specification_id'].queryset = MonoblokSpecification.objects.filter(author=request.user)
            self.fields['projector_specification_id'].queryset = ProjectorSpecification.objects.filter(author=request.user)
            self.fields['whiteboard_specification_id'].queryset = WhiteboardSpecification.objects.filter(author=request.user)
        else:
            for field in [
                'computer_specification_id', 'printer_specification_id', 'extender_specification_id',
                'router_specification_id', 'tv_specification_id', 'notebook_specification_id',
                'monoblok_specification_id', 'projector_specification_id', 'whiteboard_specification_id'
            ]:
                self.fields[field].queryset = self.fields[field].queryset.none()

    class Meta:
        model = Equipment
        fields = [
            'id', 'type', 'type_data', 'room', 'room_data', 'name', 'photo', 'description',
            'is_active', 'contract', 'created_at', 'computer_details', 'computer_specification_id',
            'computer_specification_data', 'disks', 'printer_char', 'printer_specification_id',
            'printer_specification_data', 'extender_char', 'extender_specification_id',
            'extender_specification_data', 'router_char', 'router_specification_id',
            'router_specification_data', 'tv_char', 'tv_specification_id',
            'tv_specification_data', 'notebook_char', 'notebook_specification_id',
            'notebook_specification_data', 'monoblok_char', 'monoblok_specification_id',
            'monoblok_specification_data', 'projector_char', 'projector_specification_id',
            'projector_specification_data', 'whiteboard_char', 'whiteboard_specification_id',
            'whiteboard_specification_data', 'status', 'qr_code_url', 'uid', 'author',
            'author_id', 'inn', 'location', 'repair_record', 'disposal_record', 'inn',
            'monitor_char', 'monitor_specification_data', 'monitor_specification_id', 'monitor_specification_data'
        ]
        read_only_fields = ['created_at', 'uid', 'author']

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None

    def validate(self, data):
        equipment_type = data.get('type')
        if not equipment_type:
            raise serializers.ValidationError("Поле type обязательно.")

        instance = getattr(self, 'instance', None)
        new_status = data.get('status', instance.status if instance else None)

        # Логика ремонта и утилизации
        if instance and new_status == 'NEEDS_REPAIR' and not instance.repair_record:
            instance._original_room = instance.room
            instance.room = None
            instance.location = 'Каталог ремонта'
            Repair.objects.create(equipment=instance)
        elif instance and new_status == 'DISPOSED' and not instance.disposal_record:
            instance.room = None
            instance.location = 'Утилизация'
            Disposal.objects.create(equipment=instance, reason="Переведено на утилизацию")

        if new_status in ['NEEDS_REPAIR', 'DISPOSED'] and 'location' in data:
            expected_location = 'Каталог ремонта' if new_status == 'NEEDS_REPAIR' else 'Утилизация'
            if data['location'] != expected_location:
                raise serializers.ValidationError(
                    f"Местоположение для состояния '{new_status}' должно быть '{expected_location}'."
                )

        type_name = equipment_type.name.lower()
        computer_details = data.get('computer_details')
        computer_specification_id = data.get('computer_specification_id')
        printer_char = data.get('printer_char')
        printer_specification_id = data.get('printer_specification_id')
        extender_char = data.get('extender_char')
        extender_specification_id = data.get('extender_specification_id')
        router_char = data.get('router_char')
        router_specification_id = data.get('router_specification_id')
        tv_char = data.get('tv_char')
        tv_specification_id = data.get('tv_specification_id')
        notebook_char = data.get('notebook_char')
        notebook_specification_id = data.get('notebook_specification_id')
        monoblok_char = data.get('monoblok_char')
        monoblok_specification_id = data.get('monoblok_specification_id')
        projector_char = data.get('projector_char')
        projector_specification_id = data.get('projector_specification_id')
        whiteboard_char = data.get('whiteboard_char')
        whiteboard_specification_id = data.get('whiteboard_specification_id')

        # Проверка для компьютеров
        is_computer = type_name in self.COMPUTER_TYPES
        if is_computer:
            if computer_details and computer_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо computer_details, либо computer_specification_id, но не оба."
                )
            if not computer_details and not computer_specification_id:
                raise serializers.ValidationError(
                    "Для компьютеров требуется указать computer_details или computer_specification_id."
                )
        elif computer_details or computer_specification_id:
            raise serializers.ValidationError(
                "Характеристики компьютеров поддерживаются только для типа 'компьютер'."
            )

        # Проверка для ноутбуков
        is_notebook = type_name in self.NOTEBOOK_TYPES
        if is_notebook:
            if notebook_char and notebook_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо notebook_char, либо notebook_specification_id, но не оба."
                )
            if not notebook_char and not notebook_specification_id:
                raise serializers.ValidationError(
                    "Для ноутбуков требуется указать notebook_char или notebook_specification_id."
                )
        elif notebook_char or notebook_specification_id:
            raise serializers.ValidationError(
                "Характеристики ноутбуков поддерживаются только для типа 'ноутбук'."
            )

        # Проверка для моноблоков
        is_monoblok = type_name in self.MONOBLOK_TYPES
        if is_monoblok:
            if monoblok_char and monoblok_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо monoblok_char, либо monoblok_specification_id, но не оба."
                )
            if not monoblok_char and not monoblok_specification_id:
                raise serializers.ValidationError(
                    "Для моноблоков требуется указать monoblok_char или monoblok_specification_id."
                )
        elif monoblok_char or monoblok_specification_id:
            raise serializers.ValidationError(
                "Характеристики моноблоков поддерживаются только для типа 'моноблок'."
            )

        # Проверка для принтеров
        is_printer = type_name in self.PRINTER_TYPES
        if is_printer:
            if printer_char and printer_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо printer_char, либо printer_specification_id, но не оба."
                )
            if not printer_char and not printer_specification_id:
                raise serializers.ValidationError(
                    "Для принтеров требуется указать printer_char или printer_specification_id."
                )
        elif printer_char or printer_specification_id:
            raise serializers.ValidationError(
                "Характеристики принтеров поддерживаются только для принтеров."
            )

        # Проверка для удлинителей
        is_extender = type_name in self.EXTENDER_TYPES
        if is_extender:
            if extender_char and extender_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо extender_char, либо extender_specification_id, но не оба."
                )
            if not extender_char and not extender_specification_id:
                raise serializers.ValidationError(
                    "Для удлинителей требуется указать extender_char или extender_specification_id."
                )
        elif extender_char or extender_specification_id:
            raise serializers.ValidationError(
                "Характеристики удлинителей поддерживаются только для удлинителей."
            )

        # Проверка для роутеров
        is_router = type_name in self.ROUTER_TYPES
        if is_router:
            if router_char and router_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо router_char, либо router_specification_id, но не оба."
                )
            if not router_char and not router_specification_id:
                raise serializers.ValidationError(
                    "Для роутеров требуется указать router_char или router_specification_id."
                )
        elif router_char or router_specification_id:
            raise serializers.ValidationError(
                "Характеристики роутеров поддерживаются только для роутеров."
            )

        # Проверка для телевизоров
        is_tv = type_name in self.TV_TYPES
        if is_tv:
            if tv_char and tv_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо tv_char, либо tv_specification_id, но не оба."
                )
            if not tv_char and not tv_specification_id:
                raise serializers.ValidationError(
                    "Для телевизоров требуется указать tv_char или tv_specification_id."
                )
        elif tv_char or tv_specification_id:
            raise serializers.ValidationError(
                "Характеристики телевизоров поддерживаются только для телевизоров."
            )

        # Проверка для проекторов
        is_projector = type_name in self.PROJECTOR_TYPES
        if is_projector:
            if projector_char and projector_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо projector_char, либо projector_specification_id, но не оба."
                )
            if not projector_char and not projector_specification_id:
                raise serializers.ValidationError(
                    "Для проекторов требуется указать projector_char или projector_specification_id."
                )
        elif projector_char or projector_specification_id:
            raise serializers.ValidationError(
                "Характеристики проекторов поддерживаются только для проекторов."
            )

        # Проверка для электронных досок
        is_whiteboard = type_name in self.WHITEBOARD_TYPES
        if is_whiteboard:
            if whiteboard_char and whiteboard_specification_id:
                raise serializers.ValidationError(
                    "Укажите либо whiteboard_char, либо whiteboard_specification_id, но не оба."
                )
            if not whiteboard_char and not whiteboard_specification_id:
                raise serializers.ValidationError(
                    "Для электронных досок требуется указать whiteboard_char или whiteboard_specification_id."
                )
        elif whiteboard_char or whiteboard_specification_id:
            raise serializers.ValidationError(
                "Характеристики электронных досок поддерживаются только для электронных досок."
            )

        return data

    def create(self, validated_data):
        computer_details_data = validated_data.pop('computer_details', None)
        computer_specification = validated_data.pop('computer_specification_id', None)
        printer_char_data = validated_data.pop('printer_char', None)
        printer_specification = validated_data.pop('printer_specification_id', None)
        extender_char_data = validated_data.pop('extender_char', None)
        extender_specification = validated_data.pop('extender_specification_id', None)
        router_char_data = validated_data.pop('router_char', None)
        router_specification = validated_data.pop('router_specification_id', None)
        tv_char_data = validated_data.pop('tv_char', None)
        tv_specification = validated_data.pop('tv_specification_id', None)
        notebook_char_data = validated_data.pop('notebook_char', None)
        notebook_specification = validated_data.pop('notebook_specification_id', None)
        monoblok_char_data = validated_data.pop('monoblok_char', None)
        monoblok_specification = validated_data.pop('monoblok_specification_id', None)
        projector_char_data = validated_data.pop('projector_char', None)
        projector_specification = validated_data.pop('projector_specification_id', None)
        whiteboard_char_data = validated_data.pop('whiteboard_char', None)
        whiteboard_specification = validated_data.pop('whiteboard_specification_id', None)

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user

        equipment = Equipment.objects.create(**validated_data)
        type_name = equipment.type.name.lower()

        if type_name in self.COMPUTER_TYPES:
            if computer_specification:
                spec = computer_specification
                if not isinstance(computer_specification, ComputerSpecification):
                    spec = ComputerSpecification.objects.get(id=computer_specification)
                
                computer_details_data = {
                    'cpu': spec.cpu,
                    'ram': spec.ram,
                    'has_keyboard': spec.has_keyboard,
                    'has_mouse': spec.has_mouse,
                    'monitor_size': spec.monitor_size,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
                ComputerDetails.objects.create(equipment=equipment, **computer_details_data)
                
                # Создание дисков из спецификации
                for disk_spec in spec.disk_specifications.all():
                    Disk.objects.create(
                        equipment=equipment,
                        disk_type=disk_spec.disk_type,
                        capacity_gb=disk_spec.capacity_gb,
                        author=request.user if request and request.user.is_authenticated else None
                    )
                
                # СОЗДАНИЕ ВИДЕОКАРТ ИЗ СПЕЦИФИКАЦИИ (точно как диски)
                for gpu_spec in spec.gpu_specifications.all():
                    GPU.objects.create(
                        equipment=equipment,
                        model=gpu_spec.model,
                        memory_gb=gpu_spec.memory_gb,
                        memory_type=gpu_spec.memory_type,
                        author=request.user if request and request.user.is_authenticated else None
                    )

        # Логика для ноутбуков
        elif type_name in self.NOTEBOOK_TYPES:
            if notebook_specification:
                spec = notebook_specification
                if not isinstance(notebook_specification, NotebookSpecification):
                    spec = NotebookSpecification.objects.get(id=notebook_specification)
                
                notebook_char_data = {
                    'cpu': spec.cpu,
                    'ram': spec.ram,
                    'monitor_size': spec.monitor_size,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
                NotebookChar.objects.create(equipment=equipment, **notebook_char_data)
                
                # Создание дисков
                for disk_spec in spec.disk_specifications.all():
                    Disk.objects.create(
                        equipment=equipment,
                        disk_type=disk_spec.disk_type,
                        capacity_gb=disk_spec.capacity_gb,
                        author=request.user if request and request.user.is_authenticated else None
                    )
                
                # СОЗДАНИЕ ВИДЕОКАРТ (точно как диски)
                for gpu_spec in spec.gpu_specifications.all():
                    GPU.objects.create(
                        equipment=equipment,
                        model=gpu_spec.model,
                        memory_gb=gpu_spec.memory_gb,
                        memory_type=gpu_spec.memory_type,
                        author=request.user if request and request.user.is_authenticated else None
                    )

        # Логика для моноблоков
        elif type_name in self.MONOBLOK_TYPES:
            if monoblok_specification:
                spec = monoblok_specification
                if not isinstance(monoblok_specification, MonoblokSpecification):
                    spec = MonoblokSpecification.objects.get(id=monoblok_specification)
                
                monoblok_char_data = {
                    'cpu': spec.cpu,
                    'ram': spec.ram,
                    'has_keyboard': spec.has_keyboard,
                    'has_mouse': spec.has_mouse,
                    'monitor_size': spec.monitor_size,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
                MonoblokChar.objects.create(equipment=equipment, specification=spec, **monoblok_char_data)
                
                # Создание дисков
                for disk_spec in spec.disk_specifications.all():
                    Disk.objects.create(
                        equipment=equipment,
                        disk_type=disk_spec.disk_type,
                        capacity_gb=disk_spec.capacity_gb,
                        author=request.user if request and request.user.is_authenticated else None
                    )
                
                # СОЗДАНИЕ ВИДЕОКАРТ (точно как диски)
                for gpu_spec in spec.gpu_specifications.all():
                    GPU.objects.create(
                        equipment=equipment,
                        model=gpu_spec.model,
                        memory_gb=gpu_spec.memory_gb,
                        memory_type=gpu_spec.memory_type,
                        author=request.user if request and request.user.is_authenticated else None
                    )

        # Логика для принтеров
        elif type_name in self.PRINTER_TYPES:
            if printer_specification:
                spec = printer_specification
                if not isinstance(printer_specification, PrinterSpecification):
                    spec = PrinterSpecification.objects.get(id=printer_specification)
                printer_char_data = {
                    'model': spec.model,
                    'color': spec.color,
                    'duplex': spec.duplex,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
            if printer_char_data:
                printer_char_data['serial_number'] = validated_data.get('inn', '')
                PrinterChar.objects.create(equipment=equipment, **printer_char_data)

        # Логика для удлинителей
        elif type_name in self.EXTENDER_TYPES:
            if extender_specification:
                spec = extender_specification
                if not isinstance(extender_specification, ExtenderSpecification):
                    spec = ExtenderSpecification.objects.get(id=extender_specification)
                extender_char_data = {
                    'ports': spec.ports,
                    'length': spec.length,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
            if extender_char_data:
                ExtenderChar.objects.create(equipment=equipment, **extender_char_data)

        # Логика для роутеров
        elif type_name in self.ROUTER_TYPES:
            if router_specification:
                spec = router_specification
                if not isinstance(router_specification, RouterSpecification):
                    spec = RouterSpecification.objects.get(id=router_specification)
                router_char_data = {
                    'model': spec.model,
                    'ports': spec.ports,
                    'wifi_standart': spec.wifi_standart,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
            if router_char_data:
                router_char_data['serial_number'] = validated_data.get('inn', '')
                RouterChar.objects.create(equipment=equipment, **router_char_data)

        # Логика для телевизоров
        elif type_name in self.TV_TYPES:
            if tv_specification:
                spec = tv_specification
                if not isinstance(tv_specification, TVSpecification):
                    spec = TVSpecification.objects.get(id=tv_specification)
                tv_char_data = {
                    'model': spec.model,
                    'screen_size': spec.screen_size,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
            if tv_char_data:
                tv_char_data['serial_number'] = validated_data.get('inn', '')
                TVChar.objects.create(equipment=equipment, **tv_char_data)

        # Логика для проекторов
        elif type_name in self.PROJECTOR_TYPES:
            if projector_specification:
                spec = projector_specification
                if not isinstance(projector_specification, ProjectorSpecification):
                    spec = ProjectorSpecification.objects.get(id=projector_specification)
                projector_char_data = {
                    'model': spec.model,
                    'lumens': spec.lumens,
                    'resolution': spec.resolution,
                    'throw_type': spec.throw_type,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
            if projector_char_data:
                ProjectorChar.objects.create(equipment=equipment, **projector_char_data)

        # Логика для электронных досок
        elif type_name in self.WHITEBOARD_TYPES:
            if whiteboard_specification:
                spec = whiteboard_specification
                if not isinstance(whiteboard_specification, WhiteboardSpecification):
                    spec = WhiteboardSpecification.objects.get(id=whiteboard_specification)
                whiteboard_char_data = {
                    'model': spec.model,
                    'screen_size': spec.screen_size,
                    'touch_type': spec.touch_type,
                    'touch_points': spec.touch_points,
                    'author': request.user if request and request.user.is_authenticated else None,
                }
            if whiteboard_char_data:
                WhiteboardChar.objects.create(equipment=equipment, **whiteboard_char_data)

        return equipment

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        original_status = instance.status

        # Извлечение данных характеристик и шаблонов
        computer_details_data = validated_data.pop('computer_details', None)
        computer_specification_id = validated_data.pop('computer_specification_id', None)
        printer_char_data = validated_data.pop('printer_char', None)
        printer_specification_id = validated_data.pop('printer_specification_id', None)
        extender_char_data = validated_data.pop('extender_char', None)
        extender_specification_id = validated_data.pop('extender_specification_id', None)
        router_char_data = validated_data.pop('router_char', None)
        router_specification_id = validated_data.pop('router_specification_id', None)
        tv_char_data = validated_data.pop('tv_char', None)
        tv_specification_id = validated_data.pop('tv_specification_id', None)
        notebook_char_data = validated_data.pop('notebook_char', None)
        notebook_specification_id = validated_data.pop('notebook_specification_id', None)
        monoblok_char_data = validated_data.pop('monoblok_char', None)
        monoblok_specification_id = validated_data.pop('monoblok_specification_id', None)
        projector_char_data = validated_data.pop('projector_char', None)
        projector_specification_id = validated_data.pop('projector_specification_id', None)
        whiteboard_char_data = validated_data.pop('whiteboard_char', None)
        whiteboard_specification_id = validated_data.pop('whiteboard_specification_id', None)
        validated_data.pop('author', None)

        # ИСПРАВЛЕНИЕ: Обработка объектов спецификаций для извлечения ID
        def get_specification_id(spec_obj):
            """Извлекает ID из объекта спецификации или возвращает None"""
            if spec_obj is None:
                return None
            elif hasattr(spec_obj, 'id'):
                return spec_obj.id
            elif isinstance(spec_obj, (int, str)):
                try:
                    return int(spec_obj)
                except (ValueError, TypeError):
                    return None
            elif isinstance(spec_obj, dict) and 'id' in spec_obj:
                return spec_obj['id']
            return spec_obj

        # Применяем обработку ко всем ID спецификаций
        computer_specification_id = get_specification_id(computer_specification_id)
        printer_specification_id = get_specification_id(printer_specification_id)
        extender_specification_id = get_specification_id(extender_specification_id)
        router_specification_id = get_specification_id(router_specification_id)
        tv_specification_id = get_specification_id(tv_specification_id)
        notebook_specification_id = get_specification_id(notebook_specification_id)
        monoblok_specification_id = get_specification_id(monoblok_specification_id)
        projector_specification_id = get_specification_id(projector_specification_id)
        whiteboard_specification_id = get_specification_id(whiteboard_specification_id)

        # Логика возврата из ремонта
        if new_status == 'WORKING' and original_status == 'NEEDS_REPAIR':
            repair = instance.repair_record
            if repair and repair.status == 'COMPLETED':
                if hasattr(instance, '_original_room') and instance._original_room:
                    validated_data['room'] = instance._original_room
                    del instance._original_room
                    validated_data['location'] = instance.room.number if instance.room else None
            elif repair and repair.status == 'FAILED':
                validated_data['status'] = 'DISPOSED'
                validated_data['room'] = None
                validated_data['location'] = 'Утилизация'
                if not instance.disposal_record:
                    Disposal.objects.create(
                        equipment=instance,
                        reason="Неудачный ремонт",
                        notes="Оборудование не подлежит восстановлению после ремонта"
                    )

        # Обновление основных полей
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        type_name = instance.type.name.lower()
        request = self.context.get('request')

        # Логика для компьютеров
        if type_name in self.COMPUTER_TYPES:
            if computer_specification_id:
                try:
                    spec = ComputerSpecification.objects.get(id=computer_specification_id)
                    computer_details_data = {
                        'cpu': spec.cpu,
                        'ram': spec.ram,
                        'storage': spec.storage,
                        'has_keyboard': spec.has_keyboard,
                        'has_mouse': spec.has_mouse,
                        'monitor_size': spec.monitor_size,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except ComputerSpecification.DoesNotExist:
                    pass  # Игнорируем несуществующие спецификации
            if computer_details_data:
                try:
                    computer_details = instance.computer_details
                    for attr, value in computer_details_data.items():
                        setattr(computer_details, attr, value)
                    computer_details.author = request.user if request and request.user.is_authenticated else computer_details.author
                    computer_details.save()
                except ComputerDetails.DoesNotExist:
                    ComputerDetails.objects.create(equipment=instance, **computer_details_data)
            elif hasattr(instance, 'computer_details'):
                instance.computer_details.delete()

        # Логика для ноутбуков
        elif type_name in self.NOTEBOOK_TYPES:
            if notebook_specification_id:
                try:
                    spec = NotebookSpecification.objects.get(id=notebook_specification_id)
                    notebook_char_data = {
                        'cpu': spec.cpu,
                        'ram': spec.ram,
                        'storage': spec.storage,
                        'monitor_size': spec.monitor_size,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except NotebookSpecification.DoesNotExist:
                    pass
            if notebook_char_data:
                try:
                    notebook_char = instance.notebook_char
                    for attr, value in notebook_char_data.items():
                        setattr(notebook_char, attr, value)
                    notebook_char.author = request.user if request and request.user.is_authenticated else notebook_char.author
                    notebook_char.save()
                except NotebookChar.DoesNotExist:
                    NotebookChar.objects.create(equipment=instance, **notebook_char_data)
            elif hasattr(instance, 'notebook_char'):
                instance.notebook_char.delete()

        # Логика для моноблоков
        elif type_name in self.MONOBLOK_TYPES:
            if monoblok_specification_id:
                try:
                    spec = MonoblokSpecification.objects.get(id=monoblok_specification_id)
                    monoblok_char_data = {
                        'cpu': spec.cpu,
                        'ram': spec.ram,
                        'storage': spec.storage,
                        'has_keyboard': spec.has_keyboard,
                        'has_mouse': spec.has_mouse,
                        'monitor_size': spec.monitor_size,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except MonoblokSpecification.DoesNotExist:
                    pass
            if monoblok_char_data:
                try:
                    monoblok_char = instance.monoblok_char
                    for attr, value in monoblok_char_data.items():
                        setattr(monoblok_char, attr, value)
                    monoblok_char.author = request.user if request and request.user.is_authenticated else monoblok_char.author
                    monoblok_char.save()
                except MonoblokChar.DoesNotExist:
                    MonoblokChar.objects.create(equipment=instance, **monoblok_char_data)
            elif hasattr(instance, 'monoblok_char'):
                instance.monoblok_char.delete()

        # Логика для принтеров
        elif type_name in self.PRINTER_TYPES:
            if printer_specification_id:
                try:
                    spec = PrinterSpecification.objects.get(id=printer_specification_id)
                    printer_char_data = {
                        'model': spec.model,
                        'color': spec.color,
                        'duplex': spec.duplex,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except PrinterSpecification.DoesNotExist:
                    pass
            if printer_char_data:
                try:
                    printer_char = instance.printer_char
                    for attr, value in printer_char_data.items():
                        setattr(printer_char, attr, value)
                    printer_char.serial_number = str(instance.inn) if instance.inn else printer_char.serial_number
                    printer_char.author = request.user if request and request.user.is_authenticated else printer_char.author
                    printer_char.save()
                except PrinterChar.DoesNotExist:
                    printer_char_data['serial_number'] = str(instance.inn) if instance.inn else ''
                    PrinterChar.objects.create(equipment=instance, **printer_char_data)
            elif hasattr(instance, 'printer_char'):
                instance.printer_char.delete()

        # Логика для удлинителей
        elif type_name in self.EXTENDER_TYPES:
            if extender_specification_id:
                try:
                    spec = ExtenderSpecification.objects.get(id=extender_specification_id)
                    extender_char_data = {
                        'ports': spec.ports,
                        'length': spec.length,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except ExtenderSpecification.DoesNotExist:
                    pass
            if extender_char_data:
                try:
                    extender_char = instance.extender_char
                    for attr, value in extender_char_data.items():
                        setattr(extender_char, attr, value)
                    extender_char.author = request.user if request and request.user.is_authenticated else extender_char.author
                    extender_char.save()
                except ExtenderChar.DoesNotExist:
                    ExtenderChar.objects.create(equipment=instance, **extender_char_data)
            elif hasattr(instance, 'extender_char'):
                instance.extender_char.delete()

        # Логика для роутеров
        elif type_name in self.ROUTER_TYPES:
            if router_specification_id:
                try:
                    spec = RouterSpecification.objects.get(id=router_specification_id)
                    router_char_data = {
                        'model': spec.model,
                        'ports': spec.ports,
                        'wifi_standart': spec.wifi_standart,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except RouterSpecification.DoesNotExist:
                    pass
            if router_char_data:
                try:
                    router_char = instance.router_char
                    for attr, value in router_char_data.items():
                        setattr(router_char, attr, value)
                    router_char.serial_number = str(instance.inn) if instance.inn else router_char.serial_number
                    router_char.author = request.user if request and request.user.is_authenticated else router_char.author
                    router_char.save()
                except RouterChar.DoesNotExist:
                    router_char_data['serial_number'] = str(instance.inn) if instance.inn else ''
                    RouterChar.objects.create(equipment=instance, **router_char_data)
            elif hasattr(instance, 'router_char'):
                instance.router_char.delete()

        # Логика для телевизоров
        elif type_name in self.TV_TYPES:
            if tv_specification_id:
                try:
                    spec = TVSpecification.objects.get(id=tv_specification_id)
                    tv_char_data = {
                        'model': spec.model,
                        'screen_size': spec.screen_size,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except TVSpecification.DoesNotExist:
                    pass
            if tv_char_data:
                try:
                    tv_char = instance.tv_char
                    for attr, value in tv_char_data.items():
                        setattr(tv_char, attr, value)
                    tv_char.serial_number = str(instance.inn) if instance.inn else tv_char.serial_number
                    tv_char.author = request.user if request and request.user.is_authenticated else tv_char.author
                    tv_char.save()
                except TVChar.DoesNotExist:
                    tv_char_data['serial_number'] = str(instance.inn) if instance.inn else ''
                    TVChar.objects.create(equipment=instance, **tv_char_data)
            elif hasattr(instance, 'tv_char'):
                instance.tv_char.delete()

        # Логика для проекторов
        elif type_name in self.PROJECTOR_TYPES:
            if projector_specification_id:
                try:
                    spec = ProjectorSpecification.objects.get(id=projector_specification_id)
                    projector_char_data = {
                        'model': spec.model,
                        'lumens': spec.lumens,
                        'resolution': spec.resolution,
                        'throw_type': spec.throw_type,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                except ProjectorSpecification.DoesNotExist:
                    pass
            if projector_char_data:
                try:
                    projector_char = instance.projector_char
                    for attr, value in projector_char_data.items():
                        setattr(projector_char, attr, value)
                    projector_char.author = request.user if request and request.user.is_authenticated else projector_char.author
                    projector_char.save()
                except ProjectorChar.DoesNotExist:
                    ProjectorChar.objects.create(equipment=instance, **projector_char_data)
            elif hasattr(instance, 'projector_char'):
                instance.projector_char.delete()

        # Логика для электронных досок
        elif type_name in self.WHITEBOARD_TYPES:
            if whiteboard_specification_id:
                try:
                    spec = WhiteboardSpecification.objects.get(id=whiteboard_specification_id)
                    whiteboard_char_data = {
                        'model': spec.model,
                        'screen_size': spec.screen_size,
                        'touch_type': spec.touch_type,
                        'author': request.user if request and request.user.is_authenticated else None,
                    }
                    # Убрал 'touch_points' так как его нет в модели WhiteboardSpecification
                except WhiteboardSpecification.DoesNotExist:
                    pass
            if whiteboard_char_data:
                try:
                    whiteboard_char = instance.whiteboard_char
                    for attr, value in whiteboard_char_data.items():
                        setattr(whiteboard_char, attr, value)
                    whiteboard_char.author = request.user if request and request.user.is_authenticated else whiteboard_char.author
                    whiteboard_char.save()
                except WhiteboardChar.DoesNotExist:
                    WhiteboardChar.objects.create(equipment=instance, **whiteboard_char_data)
            elif hasattr(instance, 'whiteboard_char'):
                instance.whiteboard_char.delete()

        return instance


class MovementHistorySerializer(serializers.ModelSerializer):
    equipment = serializers.StringRelatedField()
    from_room = serializers.StringRelatedField()
    to_room = serializers.StringRelatedField()

    class Meta:
        model = MovementHistory
        fields = [
            'id',
            'equipment',
            'from_room',
            'to_room',
            'moved_at',
        ]


class MoveEquipmentSerializer(serializers.Serializer):
    equipment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        required=True
    )
    from_room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        required=True
    )
    to_room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        required=True
    )

    def validate(self, data):
        equipment_ids = data['equipment_ids']
        from_room = data['from_room_id']
        to_room = data['to_room_id']

        # Проверяем, что оборудование существует и принадлежит from_room
        equipments = Equipment.objects.filter(id__in=equipment_ids, room=from_room)
        if equipments.count() != len(equipment_ids):
            raise serializers.ValidationError("Некоторые ID оборудования не найдены или не принадлежат указанному кабинету")

        # Проверяем, что from_room и to_room не совпадают
        if from_room == to_room:
            raise serializers.ValidationError("Исходный и целевой кабинеты должны быть разными")

        return data



class BulkEquipmentSerializer(serializers.Serializer):
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=EquipmentType.objects.all(),
        required=True
    )
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(),
        required=False,
        allow_null=True
    )
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=Equipment.STATUS_CHOICES,
        default='NEW'
    )
    contract_id = serializers.PrimaryKeyRelatedField(
        queryset=ContractDocument.objects.all(),
        required=False,
        allow_null=True
    )
    count = serializers.IntegerField(min_value=1, max_value=100, required=True)
    name_prefix = serializers.CharField(max_length=200, required=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    # Характеристики
    computer_details = ComputerDetailsSerializer(required=False, allow_null=True)
    printer_char = PrinterCharSerializer(required=False, allow_null=True)
    extender_char = ExtenderCharSerializer(required=False, allow_null=True)
    router_char = RouterCharSerializer(required=False, allow_null=True)
    tv_char = TVCharSerializer(required=False, allow_null=True)
    notebook_char = NotebookCharSerializer(required=False, allow_null=True)
    monoblok_char = MonoblokCharSerializer(required=False, allow_null=True)
    projector_char = ProjectorCharSerializer(required=False, allow_null=True)
    whiteboard_char = WhiteboardCharSerializer(required=False, allow_null=True)
    disks = DiskSerializer(many=True, required=False, allow_null=True)
    monitor_char = MonitorCharSerializer(required=False, allow_null=True)
    


    # Спецификации
    computer_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=ComputerSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    printer_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=PrinterSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    extender_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=ExtenderSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    router_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=RouterSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    tv_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=TVSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    notebook_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=NotebookSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    monoblok_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=MonoblokSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    projector_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=ProjectorSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    whiteboard_specification_id = serializers.PrimaryKeyRelatedField(
        queryset=WhiteboardSpecification.objects.all(),
        required=False,
        allow_null=True
    )
    disk_specifications = DiskSpecificationSerializer(
        many=True, 
        required=False, 
        allow_null=True
    )
    monitor_specification_id = serializers.PrimaryKeyRelatedField(
    queryset=MonitorSpecification.objects.all(),
    required=False,
    allow_null=True
    )

    def validate(self, data):
        equipment_type = data.get('type_id')
        if not equipment_type:
            raise serializers.ValidationError({"type_id": "Тип оборудования обязателен."})

        equipment_type_name = equipment_type.name.lower()
        type_specific_fields = {
            'компьютер': {
                'details': data.get('computer_details'),
                'spec_id': data.get('computer_specification_id'),
                'error_msg': "Для компьютеров укажите либо computer_details, либо computer_specification_id."
            },
            'принтер': {
                'details': data.get('printer_char'),
                'spec_id': data.get('printer_specification_id'),
                'error_msg': "Для принтеров укажите либо printer_char, либо printer_specification_id."
            },
            'удлинитель': {
                'details': data.get('extender_char'),
                'spec_id': data.get('extender_specification_id'),
                'error_msg': "Для удлинителей укажите либо extender_char, либо extender_specification_id."
            },
            'роутер': {
                'details': data.get('router_char'),
                'spec_id': data.get('router_specification_id'),
                'error_msg': "Для роутеров укажите либо router_char, либо router_specification_id."
            },
            'телевизор': {
                'details': data.get('tv_char'),
                'spec_id': data.get('tv_specification_id'),
                'error_msg': "Для телевизоров укажите либо tv_char, либо tv_specification_id."
            },
            'ноутбук': {
                'details': data.get('notebook_char'),
                'spec_id': data.get('notebook_specification_id'),
                'error_msg': "Для ноутбуков укажите либо notebook_char, либо notebook_specification_id."
            },
            'моноблок': {
                'details': data.get('monoblok_char'),
                'spec_id': data.get('monoblok_specification_id'),
                'error_msg': "Для моноблоков укажите либо monoblok_char, либо monoblok_specification_id."
            },
            'проектор': {
                'details': data.get('projector_char'),
                'spec_id': data.get('projector_specification_id'),
                'error_msg': "Для проекторов укажите либо projector_char, либо projector_specification_id."
            },
            'электронная доска': {
                'details': data.get('whiteboard_char'),
                'spec_id': data.get('whiteboard_specification_id'),
                'error_msg': "Для электронных досок укажите либо whiteboard_char, либо whiteboard_specification_id."
            },
            'монитор': {
                'details': data.get('monitor_char'),
                'spec_id': data.get('monitor_specification_id'),
                'error_msg': "Для мониторов укажите либо monitor_char, либо monitor_specification_id."
            },
        }

        # Проверка соответствия характеристик типу оборудования
        for type_name, fields in type_specific_fields.items():
            details = fields['details']
            spec_id = fields['spec_id']
            error_msg = fields['error_msg']

            if equipment_type_name == type_name:
                if details and spec_id:
                    raise serializers.ValidationError(error_msg + " Нельзя указывать оба одновременно.")
                if not details and not spec_id:
                    raise serializers.ValidationError(error_msg + " Необходимо указать хотя бы одно.")
            else:
                if details or spec_id:
                    raise serializers.ValidationError(
                        f"Характеристики {type_name} не поддерживаются для типа оборудования {equipment_type_name}."
                    )

        # Проверка существования комнаты
        if data.get('room_id') and not Room.objects.filter(id=data['room_id'].id).exists():
            raise serializers.ValidationError({"room_id": "Кабинет не найден"})

        return data

    def create(self, validated_data):
        count = validated_data.pop('count')
        name_prefix = validated_data.pop('name_prefix')
        author = validated_data.pop('author_id', None)
        request = self.context.get('request')

        # Устанавливаем автора
        if not author and request and request.user.is_authenticated:
            author = request.user

        # Извлекаем характеристики и спецификации
        computer_details_data = validated_data.pop('computer_details', None)
        printer_char_data = validated_data.pop('printer_char', None)
        extender_char_data = validated_data.pop('extender_char', None)
        router_char_data = validated_data.pop('router_char', None)
        tv_char_data = validated_data.pop('tv_char', None)
        notebook_char_data = validated_data.pop('notebook_char', None)
        monoblok_char_data = validated_data.pop('monoblok_char', None)
        projector_char_data = validated_data.pop('projector_char', None)
        whiteboard_char_data = validated_data.pop('whiteboard_char', None)
        disks_data = validated_data.pop('disks', None)
        monitor_char_data = validated_data.pop('monitor_char', None)


        computer_spec = validated_data.pop('computer_specification_id', None)
        printer_spec = validated_data.pop('printer_specification_id', None)
        extender_spec = validated_data.pop('extender_specification_id', None)
        router_spec = validated_data.pop('router_specification_id', None)
        tv_spec = validated_data.pop('tv_specification_id', None)
        notebook_spec = validated_data.pop('notebook_specification_id', None)
        monoblok_spec = validated_data.pop('monoblok_specification_id', None)
        projector_spec = validated_data.pop('projector_specification_id', None)
        whiteboard_spec = validated_data.pop('whiteboard_specification_id', None)
        disk_specifications_data = validated_data.pop('disk_specifications', None)
        monitor_spec = validated_data.pop('monitor_specification_id', None)

        equipments = []

        # Подготовка данных характеристик из спецификаций
        if computer_spec:
            computer_details_data = {
                'cpu': computer_spec.cpu,
                'ram': computer_spec.ram,
                'has_keyboard': computer_spec.has_keyboard,
                'has_mouse': computer_spec.has_mouse,
            }
        if notebook_spec:
            notebook_char_data = {
                'cpu': notebook_spec.cpu,
                'ram': notebook_spec.ram,
                'monitor_size': notebook_spec.monitor_size,
            }
        if monoblok_spec:
            monoblok_char_data = {
                'cpu': monoblok_spec.cpu,
                'ram': monoblok_spec.ram,
                'has_keyboard': monoblok_spec.has_keyboard,
                'has_mouse': monoblok_spec.has_mouse,
                'monitor_size': monoblok_spec.monitor_size,
            }
        if monitor_spec:  # Добавлено
            monitor_char_data = {
                'model': monitor_spec.model,
                'screen_size': monitor_spec.screen_size,
                'resolution': monitor_spec.resolution,
                'panel_type': monitor_spec.panel_type,
                'refresh_rate': monitor_spec.refresh_rate,
            }
        if printer_spec:
            printer_char_data = {
                'model': printer_spec.model,
                'serial_number': printer_spec.serial_number,
                'color': printer_spec.color,
                'duplex': printer_spec.duplex,
            }
        if extender_spec:
            extender_char_data = {
                'ports': extender_spec.ports,
                'length': extender_spec.length,
            }
        if router_spec:
            router_char_data = {
                'model': router_spec.model,
                'serial_number': router_spec.serial_number,
                'ports': router_spec.ports,
                'wifi_standart': router_spec.wifi_standart,
            }
        if tv_spec:
            tv_char_data = {
                'model': tv_spec.model,
                'serial_number': tv_spec.serial_number,
                'screen_size': tv_spec.screen_size,
            }
        if projector_spec:
            projector_char_data = {
                'model': projector_spec.model,
                'lumens': projector_spec.lumens,
                'resolution': projector_spec.resolution,
                'throw_type': projector_spec.throw_type,
            }
        if whiteboard_spec:
            whiteboard_char_data = {
                'model': whiteboard_spec.model,
                'screen_size': whiteboard_spec.screen_size,
                'touch_type': whiteboard_spec.touch_type,
            }


        for i in range(count):
            equipment_data = {
                'type': validated_data['type_id'],
                'room': validated_data.get('room_id'),
                'name': f"{name_prefix} {i + 1}",
                'description': validated_data.get('description', ''),
                'status': validated_data['status'],
                'contract': validated_data.get('contract_id'),
                'author': author,
                'inn': 0,
                'is_active': True
            }

            equipment = Equipment.objects.create(**equipment_data)
            equipment_type_name = equipment.type.name.lower()

            # Создание характеристик и дисков для компьютеров
            if equipment_type_name == 'компьютер' and computer_details_data:
                ComputerDetails.objects.create(equipment=equipment, **computer_details_data)
                
                # Создаем диски из спецификации
                if computer_spec:
                    for disk_spec in computer_spec.disk_specifications.all():
                        Disk.objects.create(
                            equipment=equipment,
                            disk_type=disk_spec.disk_type,
                            capacity_gb=disk_spec.capacity_gb,
                            author=author
                        )

            # Создание характеристик и дисков для ноутбуков
            elif equipment_type_name == 'ноутбук' and notebook_char_data:
                NotebookChar.objects.create(equipment=equipment, **notebook_char_data)
                
                # Создаем диски из спецификации
                if notebook_spec:
                    for disk_spec in notebook_spec.disk_specifications.all():
                        Disk.objects.create(
                            equipment=equipment,
                            disk_type=disk_spec.disk_type,
                            capacity_gb=disk_spec.capacity_gb,
                            author=author
                        )

            # Создание характеристик и дисков для моноблоков
            elif equipment_type_name == 'моноблок' and monoblok_char_data:
                MonoblokChar.objects.create(equipment=equipment, **monoblok_char_data)
                
                # Создаем диски из спецификации
                if monoblok_spec:
                    for disk_spec in monoblok_spec.disk_specifications.all():
                        Disk.objects.create(
                            equipment=equipment,
                            disk_type=disk_spec.disk_type,
                            capacity_gb=disk_spec.capacity_gb,
                            author=author
                        )

            # Остальные типы оборудования...
            elif equipment_type_name == 'монитор' and monitor_char_data:  # Добавлено
                monitor_char_data['serial_number'] = str(equipment.inn) if equipment.inn else ''
                MonitorChar.objects.create(equipment=equipment, **monitor_char_data)
            elif equipment_type_name in ['принтер', 'мфу'] and printer_char_data:
                printer_char_data['serial_number'] = str(equipment.inn) if equipment.inn else ''
                PrinterChar.objects.create(equipment=equipment, **printer_char_data)
            elif equipment_type_name in ['удлинитель', 'сетевой фильтр'] and extender_char_data:
                ExtenderChar.objects.create(equipment=equipment, **extender_char_data)
            elif equipment_type_name == 'роутер' and router_char_data:
                router_char_data['serial_number'] = str(equipment.inn) if equipment.inn else ''
                RouterChar.objects.create(equipment=equipment, **router_char_data)
            elif equipment_type_name == 'телевизор' and tv_char_data:
                tv_char_data['serial_number'] = str(equipment.inn) if equipment.inn else ''
                TVChar.objects.create(equipment=equipment, **tv_char_data)
            elif equipment_type_name == 'проектор' and projector_char_data:
                ProjectorChar.objects.create(equipment=equipment, **projector_char_data)
            elif equipment_type_name == 'электронная доска' and whiteboard_char_data:
                WhiteboardChar.objects.create(equipment=equipment, **whiteboard_char_data)


            equipments.append(equipment)

        return equipments

from django.utils import timezone
now = timezone.now()

class EquipmentActionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    inn = serializers.IntegerField()

from django.shortcuts import get_object_or_404

class BulkEquipmentInnUpdateSerializer(serializers.Serializer):
    equipments = serializers.ListField(
        child=EquipmentActionSerializer(),
        min_length=1
    )

    def validate(self, data):
        equipment_data = data['equipments']
        equipment_ids = [item.get('id') for item in equipment_data]
        inns = [item.get('inn') for item in equipment_data]

        # Проверяем, что все объекты содержат 'id' и 'inn'
        if not all('id' in item and 'inn' in item for item in equipment_data):
            raise serializers.ValidationError("Каждый объект должен содержать 'id' и 'inn'")

        # Проверяем, что все ID существуют
        existing_equipments = Equipment.objects.filter(id__in=equipment_ids)
        if existing_equipments.count() != len(equipment_ids):
            raise serializers.ValidationError("Некоторые ID оборудования не найдены")

        # Проверяем, что все оборудования принадлежат текущему пользователю
        user = self.context['request'].user
        if existing_equipments.filter(author=user).count() != len(equipment_ids):
            raise serializers.ValidationError("Вы можете обновлять только своё оборудование")

        # Проверяем уникальность ИНН
        if len(inns) != len(set(inns)):
            raise serializers.ValidationError("ИНН должны быть уникальными")

        return data

    def update(self, instance, validated_data):
        equipment_data = validated_data['equipments']
        equipments = []
        user = self.context.get('request').user

        for item in equipment_data:
            equipment_id = item.get('id')
            new_inn = item.get('inn')

            equipment = get_object_or_404(Equipment, id=equipment_id)
            equipment.inn = new_inn
            equipment.save()

            # Обновляем связанные характеристики (если они есть)
            if hasattr(equipment, 'printer_char'):
                equipment.printer_char.author = user
                equipment.printer_char.updated_at = timezone.now()
                equipment.printer_char.save()
            elif hasattr(equipment, 'extender_char'):
                equipment.extender_char.author = user
                equipment.extender_char.updated_at = timezone.now()
                equipment.extender_char.save()
            elif hasattr(equipment, 'router_char'):
                equipment.router_char.author = user
                equipment.router_char.updated_at = timezone.now()
                equipment.router_char.save()
            elif hasattr(equipment, 'tv_char'):
                equipment.tv_char.author = user
                equipment.tv_char.updated_at = timezone.now()
                equipment.tv_char.save()
            elif hasattr(equipment, 'notebook_details'):
                equipment.notebook_details.author = user
                equipment.notebook_details.save()  # Нет updated_at, только created_at
            elif hasattr(equipment, 'monoblok_details'):
                equipment.monoblok_details.author = user
                equipment.monoblok_details.save()  # Нет updated_at
            elif hasattr(equipment, 'projector_char'):
                equipment.projector_char.author = user
                equipment.projector_char.updated_at = timezone.now()
                equipment.projector_char.save()
            elif hasattr(equipment, 'whiteboard_char'):
                equipment.whiteboard_char.author = user
                equipment.whiteboard_char.updated_at = timezone.now()
                equipment.whiteboard_char.save()
            elif hasattr(equipment, 'computer_details'):
                equipment.computer_details.author = user
                equipment.computer_details.save()  # Нет updated_at

            equipments.append(equipment)

        return equipments

class CustomEquipmentSerializer(serializers.Serializer):
    userId = serializers.IntegerField(source='author.id')
    id = serializers.IntegerField()
    title = serializers.CharField(source='name')

    def get_body(self, obj):
        # Собираем все остальные поля в словарь
        extra_data = {
            'type': obj.type_id if obj.type else None,
            'room': obj.room_id if obj.room else None,
            'photo': str(obj.photo) if obj.photo else None,
            'description': obj.description or 'No description',
            'status': obj.status,
            'created_at': obj.created_at.isoformat() if obj.created_at else None,
            'is_active': obj.is_active,
            'inn': obj.inn,
            'contract': obj.contract_id if obj.contract else None,
            'uid': str(obj.uid),
            'qr_code': str(obj.qr_code) if obj.qr_code else None
        }
        # Преобразуем в JSON-строку
        return json.dumps(extra_data)

    body = serializers.SerializerMethodField(method_name='get_body')

    class Meta:
        fields = ['userId', 'id', 'title', 'body']



class RepairSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Repair с информацией об исходном кабинете.
    """
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_type = serializers.CharField(source='equipment.type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    original_room_data = RoomSerializer(source='original_room', read_only=True)

    class Meta:
        model = Repair
        fields = [
            'id', 'equipment', 'equipment_name', 'equipment_type',
            'start_date', 'end_date', 'status', 'status_display',
            'notes', 'original_room', 'original_room_data'
        ]
        read_only_fields = ['id', 'equipment_name', 'equipment_type', 'start_date', 'original_room']

    def validate(self, data):
        """
        Проверка статуса ремонта и оборудования.
        """
        # Если меняем статус существующей записи
        if self.instance and 'status' in data:
            # Проверяем, что статус меняется только для активного ремонта
            if self.instance.status != 'IN_PROGRESS':
                raise serializers.ValidationError({
                    "status": "Невозможно изменить статус завершенного ремонта."
                })

        # Если создаем новую запись
        if not self.instance and 'equipment' in data:
            equipment = data['equipment']

            # Проверяем, что для этого оборудования еще нет записи о ремонте
            if hasattr(equipment, 'repair_record'):
                raise serializers.ValidationError({
                    "equipment": "Для этого оборудования уже существует запись о ремонте."
                })

            # Проверяем, что оборудование не утилизировано
            if equipment.status == 'DISPOSED':
                raise serializers.ValidationError({
                    "equipment": "Невозможно отправить на ремонт утилизированное оборудование."
                })

        return data

    def create(self, validated_data):
        """
        Создание записи о ремонте.
        Автоматически обновляет статус оборудования и сохраняет исходный кабинет.
        """
        # Сохраняем исходный кабинет и создаем запись о ремонте
        repair = Repair.objects.create(**validated_data)

        return repair


class DisposalSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Disposal с информацией о последнем кабинете.
    """
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    equipment_type = serializers.CharField(source='equipment.type.name', read_only=True)
    original_room_data = RoomSerializer(source='original_room', read_only=True)

    class Meta:
        model = Disposal
        fields = [
            'id', 'equipment', 'equipment_name', 'equipment_type',
            'disposal_date', 'reason', 'notes', 'original_room', 'original_room_data'
        ]
        read_only_fields = ['id', 'equipment_name', 'equipment_type', 'disposal_date', 'original_room']

    def validate(self, data):
        """
        Проверка оборудования для утилизации.
        """
        # Если создаем новую запись
        if not self.instance and 'equipment' in data:
            equipment = data['equipment']

            # Проверяем, что для этого оборудования еще нет записи об утилизации
            if hasattr(equipment, 'disposal_record'):
                raise serializers.ValidationError({
                    "equipment": "Для этого оборудования уже существует запись об утилизации."
                })

            # Проверяем, что указана причина утилизации
            if 'reason' not in data or not data['reason']:
                raise serializers.ValidationError({
                    "reason": "Необходимо указать причину утилизации."
                })

        return data

    def create(self, validated_data):
        """
        Создание записи об утилизации.
        Автоматически обновляет статус оборудования и сохраняет исходный кабинет.
        """
        # Создаем запись об утилизации
        disposal = Disposal.objects.create(**validated_data)

        return disposal
    
