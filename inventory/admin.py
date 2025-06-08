from django.contrib import admin
from django import forms
from django.shortcuts import render, redirect
from .models import (Equipment, EquipmentType, ComputerDetails,
                     ComputerSpecification, MovementHistory, ContractDocument,
                     RouterChar, PrinterChar, TVChar, ExtenderChar,
                     PrinterSpecification, ExtenderSpecification, TVSpecification,
                     RouterSpecification, MonoblokSpecification, NotebookSpecification,
                     ProjectorSpecification, WhiteboardSpecification, Disk, DiskSpecification,
                     MonitorChar, MonitorSpecification)  # Добавляем MonitorChar и MonitorSpecification
from university.models import Room

class MoveEquipmentForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    new_room = forms.ModelChoiceField(queryset=Room.objects.all(), label="Выбери новый кабинет")

class EquipmentAdminForm(forms.ModelForm):
    computer_specification = forms.ModelChoiceField(
        queryset=ComputerSpecification.objects.all(),
        required=False,
        label="Шаблон спецификации",
        help_text="Выберите шаблон для автозаполнения характеристик компьютера"
    )

    class Meta:
        model = Equipment
        fields = '__all__'

class ComputerDetailsInline(admin.StackedInline):
    model = ComputerDetails
    can_delete = True
    extra = 0

    def has_add_permission(self, request, obj=None):
        if obj and obj.type.name.lower() == 'компьютер':
            return True
        return False

    def has_change_permission(self, request, obj=None):
        if obj and obj.type.name.lower() == 'компьютер':
            return True
        return False

class DiskInline(admin.TabularInline):
   model = Disk
   extra = 1

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    form = EquipmentAdminForm
    list_display = ('id', 'name', 'type', 'get_room_name', 'is_active', 'author', 'created_at')
    search_fields = ['name', 'description', 'inn']
    list_filter = ('is_active', 'type', 'room', 'author',)
    actions = ['move_equipment']
    inlines = [ComputerDetailsInline, DiskInline]

    def get_room_name(self, obj):
        if obj.room:
            return obj.room.number
        return "Без кабинета"
    get_room_name.short_description = "Номер кабинета"

    def move_equipment(self, request, queryset):
        if 'apply' in request.POST:
            form = MoveEquipmentForm(request.POST)
            if form.is_valid():
                to_room = form.cleaned_data['new_room']
                for equipment in queryset:
                    MovementHistory.objects.create(
                        equipment=equipment,
                        from_room=equipment.room,
                        to_room=to_room
                    )
                    equipment.room = to_room
                    equipment.save()
                self.message_user(request, f"Оборудование перемещено в кабинет {to_room.number}.")
                return redirect('..')
        else:
            form = MoveEquipmentForm()

        return render(
            request,
            'admin/move_equipment.html',
            {'equipments': queryset, 'form': form}
        )

    move_equipment.short_description = "Переместить оборудование"

    def save_model(self, request, obj, form, change):
        if not change:  # Только при создании
            obj.author = request.user
        super().save_model(request, obj, form, change)
        
        computer_specification = form.cleaned_data.get('computer_specification')
        if computer_specification and obj.type.name.lower() == 'компьютер':
            try:
                computer_details = obj.computer_details
                computer_details.cpu = computer_specification.cpu
                computer_details.ram = computer_specification.ram
                computer_details.has_keyboard = computer_specification.has_keyboard
                computer_details.has_mouse = computer_specification.has_mouse
                computer_details.monitor_size = computer_specification.monitor_size
                computer_details.save()
            except ComputerDetails.DoesNotExist:
                ComputerDetails.objects.create(
                    equipment=obj,
                    cpu=computer_specification.cpu,
                    ram=computer_specification.ram,
                    has_keyboard=computer_specification.has_keyboard,
                    has_mouse=computer_specification.has_mouse,
                    monitor_size=computer_specification.monitor_size
                )
            
            # Удаляем старые диски и создаем новые из спецификации
            obj.disks.all().delete()
            for disk_spec in computer_specification.disk_specifications.all():
                Disk.objects.create(
                    equipment=obj,
                    disk_type=disk_spec.disk_type,
                    capacity_gb=disk_spec.capacity_gb,
                    author=request.user
                )

@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['name']

class DiskSpecificationInline(admin.TabularInline):
   model = DiskSpecification
   extra = 1

@admin.register(ComputerSpecification)
class ComputerSpecificationAdmin(admin.ModelAdmin):
   list_display = ('cpu', 'ram', 'has_keyboard', 'has_mouse')
   search_fields = ['cpu', 'ram', ]
   list_filter = ('has_keyboard', 'has_mouse')
   inlines = [DiskSpecificationInline]

@admin.register(ComputerDetails)
class ComputerDetailsAdmin(admin.ModelAdmin):
   list_display = ('equipment', 'cpu', 'ram', 'has_keyboard', 'has_mouse')
   search_fields = ['equipment__name', 'cpu', 'ram']
   list_filter = ('has_keyboard', 'has_mouse')

@admin.register(MovementHistory)
class MovementHistoryAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'from_room', 'to_room', 'moved_at')
    list_filter = ('moved_at',)
    search_fields = ['equipment__name']

@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'file', 'created_at')
    search_fields = ['number']
    list_filter = ('created_at',)



@admin.register(RouterChar)
class RouterCharAdmin(admin.ModelAdmin):
    list_display = ('ports', 'wifi_standart', 'author', 'serial_number', 'model')
    search_fields = ['equipment__name', 'ports', 'wifi_standart', 'author__username', 'serial_number', 'model']
    list_filter = ( 'ports', 'wifi_standart', 'author', 'serial_number', 'model')

@admin.register(PrinterChar)
class PrinterCharAdmin(admin.ModelAdmin):
    list_display = ('color', 'duplex', 'author', 'serial_number', 'model')
    search_fields = [ 'color', 'duplex', 'author__username', 'serial_number', 'model']
    list_filter = ('color', 'duplex', 'author', 'serial_number', 'model')

@admin.register(TVChar)
class TVCharAdmin(admin.ModelAdmin):
    list_display = ('screen_size', 'model', 'serial_number', 'author')
    search_fields = [ 'screen_size', 'model', 'serial_number']
    def get_author(self, obj):
        return obj.equipment.author.username if obj.equipment.author else "Неизвестно"
    list_filter = ('screen_size', 'model', 'serial_number', 'author')


@admin.register(ExtenderChar)
class ExtenderCharAdmin(admin.ModelAdmin):
    list_display = ( 'ports', 'length', 'author')
    search_fields = ['ports', 'length']
    list_filter = ('ports', 'length')

@admin.register(PrinterSpecification)
class PrinterSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'serial_number', 'color', 'duplex')
    search_fields = ['color', 'duplex']
    list_filter = ('color', 'duplex')

@admin.register(ExtenderSpecification)
class ExtenderSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'ports', 'length')
    search_fields = ['ports', 'length']
    list_filter = ('ports', 'length')

@admin.register(TVSpecification)
class TVSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'serial_number', 'screen_size')
    search_fields = ['screen_size']
    list_filter = ('screen_size',)

@admin.register(RouterSpecification)
class RouterSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'serial_number', 'ports', 'wifi_standart')
    search_fields = ['ports', 'wifi_standart']
    list_filter = ('ports', 'wifi_standart')

@admin.register(MonoblokSpecification)
class MonoblokSpecificationAdmin(admin.ModelAdmin):
   list_display = ('cpu', 'ram', 'has_keyboard', 'has_mouse', 'monitor_size')
   search_fields = ['cpu', 'ram', ]
   list_filter = ('has_keyboard', 'has_mouse')
   inlines = [DiskSpecificationInline]


@admin.register(NotebookSpecification)
class NotebookSpecificationAdmin(admin.ModelAdmin):
   list_display = ('cpu', 'ram', 'monitor_size')
   search_fields = ['cpu', 'ram', ]
   list_filter = ('cpu',)
   inlines = [DiskSpecificationInline]

@admin.register(ProjectorSpecification)
class ProjectorSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'lumens', 'resolution', 'throw_type')
    search_fields = ['model', 'lumens']
    list_filter = ('model', 'lumens')

@admin.register(WhiteboardSpecification)
class WhiteboardSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'screen_size', 'touch_type')
    search_fields = ['model']
    list_filter = ('model', )

@admin.register(Disk)
class DiskAdmin(admin.ModelAdmin):
   list_display = ('equipment', 'disk_type', 'capacity_gb', 'author', 'created_at')
   list_filter = ('disk_type', 'author')
   search_fields = ('equipment__name',)

@admin.register(DiskSpecification)
class DiskSpecificationAdmin(admin.ModelAdmin):
   list_display = ('disk_type', 'capacity_gb', 'author', 'created_at')
   list_filter = ('disk_type', 'author')


@admin.register(MonitorChar)
class MonitorCharAdmin(admin.ModelAdmin):
    list_display = ('model', 'screen_size', 'resolution', 'panel_type', 'refresh_rate', 'author', 'serial_number')
    search_fields = ['model', 'serial_number', 'screen_size']
    list_filter = ('panel_type', 'refresh_rate', 'author', 'screen_size')


@admin.register(MonitorSpecification)
class MonitorSpecificationAdmin(admin.ModelAdmin):
    list_display = ('model', 'serial_number', 'screen_size', 'resolution', 'panel_type', 'refresh_rate')
    search_fields = ['model', 'screen_size', 'resolution']
    list_filter = ('panel_type', 'refresh_rate')


# Также нужно обновить импорты в начале файла
