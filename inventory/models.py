from django.db import models
from university.models import Room
from django.utils import timezone
import uuid
from django.conf import settings



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
    valid_until = models.DateField(verbose_name="Дата действия договора", null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_ContractDocument'
    )
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата загрузки")

    def __str__(self):
        return f"Договор №{self.number}"

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договора"






class Equipment(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Новое'),
        ('WORKING', 'Рабочее'),
        ('NEEDS_REPAIR', 'Требуется ремонт'),
        ('DISPOSED', 'Утилизировано'),
    ]

    type = models.ForeignKey('EquipmentType', on_delete=models.CASCADE, related_name='equipment', verbose_name="Тип оборудования")
    room = models.ForeignKey('university.Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment', verbose_name="Кабинет")
    name = models.CharField(max_length=255, verbose_name="Название оборудования")
    photo = models.ImageField(upload_to='equipment_photos/', null=True, blank=True, verbose_name="Фото оборудования")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="Состояние")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    inn = models.IntegerField(verbose_name="ИНН")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_equipment'
    )
    contract = models.ForeignKey('ContractDocument', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Договор")

    # Новый уникальный идентификатор
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Уникальный ID")

    # QR-код для оборудования
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name="QR-код")

    def __str__(self):
        return f"{self.name} ({self.type.name})"


    def save(self, *args, **kwargs):
        import qrcode
        from io import BytesIO
        from django.core.files import File
        from PIL import Image, ImageDraw, ImageFont

        # Проверяем, нужно ли обновить QR-код
        generate_qr = False
        if not self.inn:
            # Если inn пустой, удаляем QR-код, если он есть
            if self.qr_code:
                self.qr_code.delete(save=False)
                self.qr_code = None
        elif not self.qr_code:
            # Если inn есть, но QR-кода нет, генерируем его
            generate_qr = True
        elif self.pk:  # Если объект уже существует, проверяем изменения inn
            original = Equipment.objects.get(pk=self.pk)
            if original.inn != self.inn:
                # Если inn изменился, удаляем старый QR-код и генерируем новый
                if self.qr_code:
                    self.qr_code.delete(save=False)
                generate_qr = True

        # Генерация QR-кода, если нужно
        if generate_qr:
            qr_data = f"UID: {self.uid}\nИНН: {self.inn}\nНазвание: {self.name}\nКабинет: {self.room.number if self.room else 'N/A'}"
            qr = qrcode.make(qr_data)

            # Преобразуем в RGB и рисуем текст под QR-кодом
            qr = qr.convert("RGB")
            draw = ImageDraw.Draw(qr)

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except:
                font = ImageFont.load_default()

            text = f"ИНН: {self.inn}"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Создаём новое изображение с местом под текст
            new_img = Image.new("RGB", (qr.width, qr.height + text_height + 10), "white")
            new_img.paste(qr, (0, 0))
            draw = ImageDraw.Draw(new_img)
            draw.text(((qr.width - text_width) // 2, qr.height + 5), text, fill="black", font=font)

            # Сохраняем
            buffer = BytesIO()
            new_img.save(buffer, format='PNG')
            buffer.seek(0)
            filename = f"equipment_qr_{self.uid}.png"
            self.qr_code.save(filename, File(buffer), save=False)

        # Логика изменения состояния и местоположения
        if self.pk:  # Проверяем, существует ли объект (обновление)
            original = Equipment.objects.get(pk=self.pk)
            if original.status != self.status:
                if self.status == 'NEEDS_REPAIR':
                    self._original_room = original.room  # Сохраняем исходный кабинет
                    self.room = None
                    self.location = 'Каталог ремонта'
                elif self.status == 'WORKING' and original.status == 'NEEDS_REPAIR':
                    if hasattr(self, '_original_room') and self._original_room:
                        self.room = self._original_room
                        del self._original_room  # Очищаем временное поле
                        self.location = self.room.number if self.room else None

        super().save(*args, **kwargs)

    @property
    def location(self):
        return self.room.number if self.room else getattr(self, '_location', None)

    @location.setter
    def location(self, value):
        if not self.room and value:
            self._location = value

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"




# 1. GPUSpecification - шаблоны видеокарт (аналогично DiskSpecification)
class GPUSpecification(models.Model):
    computer_specification = models.ForeignKey('ComputerSpecification', on_delete=models.CASCADE, related_name='gpu_specifications', null=True, blank=True)
    notebook_specification = models.ForeignKey('NotebookSpecification', on_delete=models.CASCADE, related_name='gpu_specifications', null=True, blank=True)
    monoblok_specification = models.ForeignKey('MonoblokSpecification', on_delete=models.CASCADE, related_name='gpu_specifications', null=True, blank=True)
    
    model = models.CharField(max_length=255, verbose_name="Модель видеокарты")

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_gpu_specifications',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model} {self.memory_gb}GB"

    class Meta:
        verbose_name = "Спецификация видеокарты"
        verbose_name_plural = "Спецификации видеокарт"


# 2. GPU - реальные видеокарты оборудования (аналогично Disk)
class GPU(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='gpus', verbose_name="Оборудование")
    model = models.CharField(max_length=255, verbose_name="Модель видеокарты")

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_gpus',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model} {self.memory_gb}GB для {self.equipment.name}"

    class Meta:
        verbose_name = "Видеокарта"
        verbose_name_plural = "Видеокарты"




class ComputerDetails(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='computer_details', verbose_name="Оборудование")
    cpu = models.CharField(max_length=255, help_text="Процессор", verbose_name="Процессор")
    ram = models.CharField(max_length=255, help_text="Оперативная память", verbose_name="Оперативная память")
    has_keyboard = models.BooleanField(default=True, help_text="Есть ли клавиатура")
    has_mouse = models.BooleanField(default=True, help_text="Есть ли мышь")

    def __str__(self):
        return f"Компьютерные характеристики для {self.equipment.name}"

    class Meta:
        verbose_name = "Компьютерные характеристики"
        verbose_name_plural = "Компьютерные характеристики"


class ComputerSpecification(models.Model):
    cpu = models.CharField(max_length=255, verbose_name="Процессор")
    ram = models.CharField(max_length=255, verbose_name="Оперативная память")
    gpus = models.ManyToManyField('GPUSpecification', verbose_name="Видеокарты", blank=True)
    disks = models.ManyToManyField('DiskSpecification', verbose_name="Накопители", blank=True)
    has_keyboard = models.BooleanField(default=True, verbose_name="Есть ли клавиатура")
    has_mouse = models.BooleanField(default=True, verbose_name="Есть ли мышь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Уникальный ID")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_computer_specifications',
        verbose_name="Автор"
    )


    def __str__(self):
        return f"{self.cpu}, {self.ram}"

    class Meta:
        verbose_name = "Компьютерная спецификация"
        verbose_name_plural = "Компьютерные спецификации"


class DiskSpecification(models.Model):
    computer_specification = models.ForeignKey('ComputerSpecification', on_delete=models.CASCADE, related_name='disk_specifications', null=True, blank=True)
    notebook_specification = models.ForeignKey('NotebookSpecification', on_delete=models.CASCADE, related_name='disk_specifications', null=True, blank=True)
    monoblok_specification = models.ForeignKey('MonoblokSpecification', on_delete=models.CASCADE, related_name='disk_specifications', null=True, blank=True)
    DISK_TYPE_CHOICES = (
        ("HDD", "HDD"),
        ("SSD", "SSD"),
        ("NVME", "NVMe"),
    )
    disk_type = models.CharField(max_length=10, choices=DISK_TYPE_CHOICES, verbose_name="Тип диска")
    capacity_gb = models.PositiveIntegerField(verbose_name="Объем (ГБ)")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_disk_specifications',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_disk_type_display()} {self.capacity_gb} ГБ"

    class Meta:
        verbose_name = "Спецификация диска"
        verbose_name_plural = "Спецификации дисков"


class Disk(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='disks', verbose_name="Оборудование")
    disk_type = models.CharField(
        max_length=10,
        choices=DiskSpecification.DISK_TYPE_CHOICES,
        verbose_name="Тип диска"
    )
    capacity_gb = models.PositiveIntegerField(verbose_name="Объем (ГБ)")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_disks',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Диск {self.get_disk_type_display()} {self.capacity_gb} ГБ для {self.equipment.name}"

    class Meta:
        verbose_name = "Диск"
        verbose_name_plural = "Диски"
 
 
class MovementHistory(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='movements', verbose_name="Оборудование")
    from_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='moved_out', verbose_name="Из кабинета")
    to_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='moved_in', verbose_name="В кабинет")
    moved_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата перемещения")
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.equipment} moved from {self.from_room} to {self.to_room} at {self.moved_at}'

    class Meta:
        verbose_name = "История перемещений"
        verbose_name_plural = "История перемещений"


class PrinterChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='printer_char', verbose_name="Оборудование")
    model = models.CharField(max_length=255, verbose_name="Модель принтера")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    color = models.BooleanField(default=False, verbose_name="Цветной")
    duplex = models.BooleanField(default=False, verbose_name="Дуплексный")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_printer',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Принтер {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Принтер Char"
        verbose_name_plural = "Принтеры Char"

class ExtenderChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='extender_char', verbose_name="Оборудование")
    ports = models.IntegerField(default=4, verbose_name="Количество портов")
    length = models.CharField(max_length=50, verbose_name="Длина кабеля")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_extender',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Удлинитель ({self.ports} портов, {self.length})"

    class Meta:
        verbose_name = "Расширитель Char"
        verbose_name_plural = "Расширители Char"

class RouterChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='router_char', verbose_name="Оборудование")
    model = models.CharField(max_length=255, verbose_name="Модель роутера")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    ports = models.IntegerField(default=4, verbose_name="Количество портов")
    wifi_standart = models.CharField(max_length=50, verbose_name="Стандарт Wi-Fi")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_router',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Роутер {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Роутер Char"
        verbose_name_plural = "Роутеры Char"


class TVChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='tv_char', verbose_name="Оборудование")
    model = models.CharField(max_length=255, verbose_name="Модель телевизора")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    screen_size = models.CharField(max_length=50, verbose_name="Размер экрана")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tv',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Телевизор {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Телевизор Char"
        verbose_name_plural = "Телевизоры Char"


class PrinterSpecification(models.Model):
    model = models.CharField(max_length=255, verbose_name="Модель принтера")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    color = models.BooleanField(default=False, verbose_name="Цветной")
    duplex = models.BooleanField(default=False, verbose_name="Дуплексный")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_printer',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Спецификация принтера {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Спецификация принтера"
        verbose_name_plural = "Спецификации принтеров"

class ExtenderSpecification(models.Model):
    ports = models.IntegerField(default=4, verbose_name="Количество портов")
    length = models.CharField(max_length=50, verbose_name="Длина кабеля")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_extender',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Удлинитель ({self.ports} портов, {self.length})"

    class Meta:
        verbose_name = "Расширитель Спецификасии"
        verbose_name_plural = "Расширители Спецификасии"

class RouterSpecification(models.Model):
    model = models.CharField(max_length=255, verbose_name="Модель роутера")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    ports = models.IntegerField(default=4, verbose_name="Количество портов")
    wifi_standart = models.CharField(max_length=50, verbose_name="Стандарт Wi-Fi")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_router',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Роутер {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Роутер Спецификасии"
        verbose_name_plural = "Роутеры Спецификасии"

class TVSpecification(models.Model):
    model = models.CharField(max_length=255, verbose_name="Модель телевизора")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    screen_size = models.CharField(max_length=50, verbose_name="Размер экрана")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_tv',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Телевизор {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Телевизор Спецификасии"
        verbose_name_plural = "Телевизоры Спецификасии"


##############################################
class NotebookChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='notebook_details', verbose_name="Ноутбук")
    cpu = models.CharField(max_length=255, help_text="Процессор", verbose_name="Процессор")
    ram = models.CharField(max_length=255, help_text="Оперативная память", verbose_name="Оперативная память")
    monitor_size = models.CharField(max_length=50, blank=True, help_text="Размер монитора", verbose_name="Размер монитора")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdchar_notebook',
        verbose_name="Автор"

    )
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Характеристики ноутбука для {self.equipment.name}"

    class Meta:
        verbose_name = "Характеристики Ноутбука"
        verbose_name_plural = "Характеристики Ноутбуков"


class NotebookSpecification(models.Model):
    cpu = models.CharField(max_length=255, help_text="Процессор", verbose_name="Процессор")
    ram = models.CharField(max_length=255, help_text="Оперативная память", verbose_name="Оперативная память")
    disks = models.ManyToManyField('DiskSpecification', verbose_name="Накопители", blank=True)
    gpus = models.ManyToManyField('GPUSpecification', verbose_name="Видеокарты", blank=True)
    monitor_size = models.CharField(max_length=50, blank=True, help_text="Размер монитора", verbose_name="Размер монитора")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createspek_notebook',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cpu}, {self.ram}"

    class Meta:
        verbose_name = "Характеристики Ноутбука"
        verbose_name_plural = "Характеристики Ноутбуков"


class MonoblokChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='monoblok_details', verbose_name="Моноблок")
    cpu = models.CharField(max_length=255, help_text="Процессор", verbose_name="Процессор")
    ram = models.CharField(max_length=255, help_text="Оперативная память", verbose_name="Оперативная память")
    has_keyboard = models.BooleanField(default=True, help_text="Есть ли клавиатура")
    has_mouse = models.BooleanField(default=True, help_text="Есть ли мышь")
    monitor_size = models.CharField(max_length=50, blank=True, help_text="Размер монитора (если есть)", verbose_name="Размер монитора")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createChar_monoblok',
        verbose_name="Автор"
    )

    def __str__(self):
        return f"Характеристики для Моноблока {self.equipment.name}"

    class Meta:
        verbose_name = "Характеристика для Моноблока"
        verbose_name_plural = "Характеристика для Моноблоков"

class MonoblokSpecification(models.Model):
    cpu = models.CharField(max_length=255, help_text="Процессор", verbose_name="Процессор")
    ram = models.CharField(max_length=255, help_text="Оперативная память", verbose_name="Оперативная память")
    disks = models.ManyToManyField('DiskSpecification', verbose_name="Накопители", blank=True)
    has_keyboard = models.BooleanField(default=True, help_text="Есть ли клавиатура")
    has_mouse = models.BooleanField(default=True, help_text="Есть ли мышь")
    gpus = models.ManyToManyField('GPUSpecification', verbose_name="Видеокарты", blank=True)
    monitor_size = models.CharField(max_length=50, blank=True, help_text="Размер монитора (если есть)", verbose_name="Размер монитора")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_monoblok',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return f"{self.cpu}, {self.ram}"

    class Meta:
        verbose_name = "Характеристика для Моноблока"
        verbose_name_plural = "Характеристика для Моноблоков"


class ProjectorChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='projector_char', verbose_name="Оборудование")
    model = models.CharField(max_length=255, verbose_name="Модель")
    lumens = models.PositiveIntegerField(verbose_name="Яркость (люмены)")
    resolution = models.CharField(max_length=50, verbose_name="Разрешение", help_text="Например, 1920x1080")
    throw_type = models.CharField(
        max_length=20,
        choices=(
            ('standard', 'Стандартный'),
            ('short', 'Короткофокусный'),
            ('ultra_short', 'Ультракороткофокусный'),
        ),
        verbose_name="Тип проекции"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdchar_projector',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Характеристики проектора"
        verbose_name_plural = "Характеристики проекторов"

    def __str__(self):
        return f"Характеристики {self.model} для {self.equipment}"

class ProjectorSpecification(models.Model):
    model = models.CharField(max_length=255, verbose_name="Модель")
    lumens = models.PositiveIntegerField(verbose_name="Яркость (люмены)")
    resolution = models.CharField(max_length=50, verbose_name="Разрешение", help_text="Например, 1920x1080")
    throw_type = models.CharField(
        max_length=20,
        choices=(
            ('standard', 'Стандартный'),
            ('short', 'Короткофокусный'),
            ('ultra_short', 'Ультракороткофокусный'),
        ),
        verbose_name="Тип проекции"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_projector',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Шаблон проектора"
        verbose_name_plural = "Шаблоны проекторов"

    def __str__(self):
        return f"Шаблон {self.model}"

# Новые модели для электронной доски
class WhiteboardChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='whiteboard_char', verbose_name="Оборудование")
    model = models.CharField(max_length=255, verbose_name="Модель")
    screen_size = models.PositiveIntegerField(verbose_name="Размер экрана (дюймы)")
    touch_type = models.CharField(
        max_length=20,
        choices=(
            ('infrared', 'Инфракрасный'),
            ('capacitive', 'Ёмкостный'),
        ),
        verbose_name="Тип сенсора"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdchar_whiteboard',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Характеристики электронной доски"
        verbose_name_plural = "Характеристики электронных досок"

    def __str__(self):
        return f"Характеристики {self.model} для {self.equipment}"

class WhiteboardSpecification(models.Model):
    model = models.CharField(max_length=255, verbose_name="Модель")
    screen_size = models.PositiveIntegerField(verbose_name="Размер экрана (дюймы)")
    touch_type = models.CharField(
        max_length=20,
        choices=(
            ('infrared', 'Инфракрасный'),
            ('capacitive', 'Ёмкостный'),
        ),
        verbose_name="Тип сенсора"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_whiteboard',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Шаблон электронной доски"
        verbose_name_plural = "Шаблоны электронных досок"

    def __str__(self):
        return f"Шаблон {self.model}"


class Repair(models.Model):
    """
    Модель для записей о ремонте оборудования.
    """
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='repair_record')
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата начала ремонта")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    status = models.CharField(
        max_length=20,
        choices=[
            ('IN_PROGRESS', 'В процессе'),
            ('COMPLETED', 'Завершён'),
            ('FAILED', 'Неудача'),
        ],
        default='IN_PROGRESS',
        verbose_name="Статус ремонта"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")

    # Дополнительные поля для отслеживания исходного местоположения
    original_room = models.ForeignKey(
        'university.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment_in_repair',
        verbose_name="Исходный кабинет"
    )

    def save(self, *args, **kwargs):
        """
        Переопределенный метод save для обработки логики ремонта.
        """
        # Если запись новая, сохраняем исходный кабинет
        if not self.pk:
            self.original_room = self.equipment.room

            # Удаляем оборудование из кабинета при отправке на ремонт
            if self.equipment.room:
                self.equipment.room = None
                self.equipment.status = 'NEEDS_REPAIR'
                self.equipment.save(update_fields=['room', 'status'])

        # Если запись существует и статус изменился
        elif self.pk:
            try:
                old_repair = Repair.objects.get(pk=self.pk)

                # Если статус изменился с "В процессе" на "Завершён"
                if old_repair.status == 'IN_PROGRESS' and self.status == 'COMPLETED':
                    # Обновляем дату завершения ремонта
                    self.end_date = timezone.now()

                    # Возвращаем оборудование в исходный кабинет
                    self.equipment.room = self.original_room
                    self.equipment.status = 'WORKING'
                    self.equipment.save(update_fields=['room', 'status'])

                # Если статус изменился с "В процессе" на "Неудача"
                elif old_repair.status == 'IN_PROGRESS' and self.status == 'FAILED':
                    # Обновляем дату завершения ремонта
                    self.end_date = timezone.now()

                    # Меняем статус оборудования на "Утилизировано"
                    self.equipment.status = 'DISPOSED'
                    self.equipment.save(update_fields=['status'])

                    # Создаем запись об утилизации, если ее еще нет
                    if not hasattr(self.equipment, 'disposal_record'):
                        Disposal.objects.create(
                            equipment=self.equipment,
                            reason="Неудачный ремонт оборудования",
                            notes=f"Автоматически создано после неудачного ремонта."
                        )

            except Repair.DoesNotExist:
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ремонт {self.equipment.name}"

    class Meta:
        verbose_name = "Ремонт"
        verbose_name_plural = "Ремонты"


class Disposal(models.Model):
    """
    Модель для записей об утилизации оборудования.
    """
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='disposal_record')
    disposal_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата утилизации")
    reason = models.TextField(verbose_name="Причина утилизации")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    # Дополнительные поля для отслеживания исходного местоположения
    original_room = models.ForeignKey(
        'university.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment_disposed',
        verbose_name="Последний кабинет"
    )

    def save(self, *args, **kwargs):
        """
        Переопределенный метод save для обработки логики утилизации.
        """
        # Если запись новая, сохраняем исходный кабинет и обновляем статус
        if not self.pk:
            self.original_room = self.equipment.room

            # Удаляем оборудование из кабинета и меняем статус
            if self.equipment.status != 'DISPOSED':
                self.equipment.room = None
                self.equipment.status = 'DISPOSED'
                self.equipment.save(update_fields=['room', 'status'])

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Утилизация {self.equipment.name}"

    class Meta:
        verbose_name = "Утилизация"
        verbose_name_plural = "Утилизации"



class MonitorChar(models.Model):
    equipment = models.OneToOneField(Equipment, on_delete=models.CASCADE, related_name='monitor_char', verbose_name="Оборудование")
    model = models.CharField(max_length=255, verbose_name="Модель монитора")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    screen_size = models.CharField(max_length=50, verbose_name="Размер экрана")
    resolution = models.CharField(max_length=50, verbose_name="Разрешение", help_text="Например, 1920x1080")
    panel_type = models.CharField(
        max_length=20,
        choices=[
            ('IPS', 'IPS'),
            ('TN', 'TN'),
            ('VA', 'VA'),
            ('OLED', 'OLED'),
        ],
        verbose_name="Тип матрицы",
        blank=True
    )
    refresh_rate = models.PositiveIntegerField(verbose_name="Частота обновления (Гц)", null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_monitor',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Монитор {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Монитор Char"
        verbose_name_plural = "Мониторы Char"


class MonitorSpecification(models.Model):
    model = models.CharField(max_length=255, verbose_name="Модель монитора")
    serial_number = models.CharField(max_length=255, verbose_name="Серийный номер")
    screen_size = models.CharField(max_length=50, verbose_name="Размер экрана")
    resolution = models.CharField(max_length=50, verbose_name="Разрешение", help_text="Например, 1920x1080")
    panel_type = models.CharField(
        max_length=20,
        choices=[
            ('IPS', 'IPS'),
            ('TN', 'TN'),
            ('VA', 'VA'),
            ('OLED', 'OLED'),
        ],
        verbose_name="Тип матрицы",
        blank=True
    )
    refresh_rate = models.PositiveIntegerField(verbose_name="Частота обновления (Гц)", null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='createdspek_monitor',
        verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Спецификация монитора {self.model} ({self.serial_number})"

    class Meta:
        verbose_name = "Спецификация монитора"
        verbose_name_plural = "Спецификации мониторов"