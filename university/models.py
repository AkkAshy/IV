from django.db import models
from django.core.files import File
import qrcode
import os
from io import BytesIO
import uuid
from django.conf import settings

class University(models.Model):  # Университет
    name = models.CharField(max_length=255, verbose_name="Название университета")
    address = models.TextField(verbose_name="Адрес")
    logo = models.ImageField(upload_to='university_logos/', null=True, blank=True, verbose_name="Логотип")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Университет"
        verbose_name_plural = "Университеты"



class Building(models.Model):   # Корпус
    university = models.ForeignKey(
        'University',
        on_delete=models.CASCADE,
        related_name='buildings',
        verbose_name="Университет"
    )

    name = models.CharField(max_length=100, verbose_name="Название корпуса")
    address = models.TextField(verbose_name="Адрес корпуса", blank=True)
    photo = models.ImageField(upload_to='building_photos/', null=True, blank=True, verbose_name="Фото корпуса")

    def __str__(self):
        return f"{self.name} — {self.university.name}"

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпуса"

class Room(models.Model): # Кабинет
    building = models.ForeignKey(
        'Building',
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name="Корпус"
    )
    floor = models.ForeignKey(
        'Floor',
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name="Этаж"
    )

    derived_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derived_rooms',
        verbose_name="Создан из кабинета"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_rooms',
        verbose_name="Автор"
    )

    number = models.CharField(max_length=20, verbose_name="Номер кабинета")
    name = models.CharField(max_length=255, blank=True, verbose_name="Название (если есть)")
    is_special = models.BooleanField(default=False, verbose_name="Специальный кабинет")
    photo = models.ImageField(upload_to='room_photos/', null=True, blank=True, verbose_name="Фото кабинета")
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Уникальный ID")
    qr_code = models.ImageField(upload_to='room_qrcodes/', null=True, blank=True, verbose_name="QR-код кабинета")


    class Meta:
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"
        unique_together = ('floor', 'number')


    def __str__(self):
        return f"{self.number} ({self.building.name})"

    def generate_qr_code(self):
        if not self.qr_code:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(str(self.uid))
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            file_name = f"room_qr_{self.uid}.png"
            self.qr_code.save(file_name, File(buffer), save=False)

    def save(self, *args, **kwargs):
        if not self.building:
            raise ValueError("Поле 'building' обязательно для заполнения")
        if not self.floor:
            raise ValueError("Поле 'floor' обязательно для заполнения")
        if not self.uid:
            self.uid = uuid.uuid4()
        self.generate_qr_code()
        super().save(*args, **kwargs)



class Faculty(models.Model):    # Факультет
    building = models.ForeignKey(
        'Building',
        on_delete=models.CASCADE,
        related_name='faculties',
        verbose_name="Корпус"
    )

    floor = models.ForeignKey(
        'Floor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faculties',
        verbose_name="Этаж"
    )

    name = models.CharField(max_length=255, verbose_name="Название факультета")
    photo = models.ImageField(upload_to='faculty_photos/', null=True, blank=True, verbose_name="Фото факультета")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Факультет"
        verbose_name_plural = "Факультеты"
        unique_together = ('building', 'name')



class Floor(models.Model): # Этаж
    building = models.ForeignKey(
        'Building',
        on_delete=models.CASCADE,
        related_name='floors',
        verbose_name="Корпус"
    )
    number = models.IntegerField(verbose_name="Номер этажа")
    description = models.TextField(blank=True, verbose_name="Описание (необязательно)")

    def __str__(self):
        return f"Этаж {self.number} — {self.building.name}"

    class Meta:
        verbose_name = "Этаж"
        verbose_name_plural = "Этажи"
        unique_together = ('building', 'number')




class RoomHistory(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='histories')
    action = models.CharField(max_length=100)  # например "Разделён"
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

class FacultyHistory(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='histories', verbose_name="Факультет")
    action = models.CharField(max_length=100, verbose_name="Действие")  # Например, "Разделён"
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return f"{self.action} — {self.faculty.name} — {self.timestamp}"

    class Meta:
        verbose_name = "История факультета"
        verbose_name_plural = "Истории факультетов"

