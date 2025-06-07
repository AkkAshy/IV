from django.db import models
from university.models import Room

class EquipmentType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название типа оборудования")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Тип оборудования"
        verbose_name_plural = "Типы оборудования"


class ContractDocument(models.Model):
    number = models.CharField(max_length=100, verbose_name="Номер договора")
    file = models.FileField(upload_to='contracts/', verbose_name="Файл договора")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата загрузки")

    def __str__(self):
        return f"Договор №{self.number}"

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договора"


class Equipment(models.Model):
    type = models.ForeignKey(EquipmentType, on_delete=models.CASCADE, related_name='equipment', verbose_name="Тип оборудования")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment', verbose_name="Кабинет")
    name = models.CharField(max_length=255, verbose_name="Название оборудования")
    photo = models.ImageField(upload_to='equipment_photos/', null=True, blank=True, verbose_name="Фото оборудования")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True )
    inn = models.CharField(max_length=12, verbose_name="ИНН")  # или IntegerField, если нужно строгое число
    contract = models.ForeignKey(ContractDocument, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Договор")

    def __str__(self):
        return f"{self.name} ({self.type.name})"
    
    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"

class ComputerDetails(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='computer_details', verbose_name="Оборудование")
    cpu = models.CharField(max_length=255, help_text="Процессор", verbose_name="Процессор")
    ram = models.CharField(max_length=255, help_text="Оперативная память", verbose_name="Оперативная память")
    storage = models.CharField(max_length=255, help_text="Накопитель (SSD/HDD)", verbose_name="Накопитель")
    has_keyboard = models.BooleanField(default=True, help_text="Есть ли клавиатура")
    has_mouse = models.BooleanField(default=True, help_text="Есть ли мышь")
    monitor_size = models.CharField(max_length=50, blank=True, help_text="Размер монитора (если есть)", verbose_name="Размер монитора")

    def __str__(self):
        return f"Компьютерные характеристики для {self.equipment.name}"
    
    class Meta:
        verbose_name = "Компьютерные характеристики"
        verbose_name_plural = "Компьютерные характеристики"





class MovementHistory(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='movements', verbose_name="Оборудование")
    from_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='moved_out', verbose_name="Из кабинета")
    to_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='moved_in', verbose_name="В кабинет")
    moved_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата перемещения")

    def __str__(self):
        return f"Перемещение {self.equipment.name} ({self.moved_at.date()})"

    class Meta:
        verbose_name = "История перемещений"
        verbose_name_plural = "История перемещений"