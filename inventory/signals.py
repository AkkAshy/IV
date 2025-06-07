from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Equipment, Repair, Disposal

@receiver(pre_save, sender=Equipment)
def handle_equipment_status_change(sender, instance, **kwargs):
    """
    Сигнал для обработки изменений статуса оборудования.
    Автоматически создает записи о ремонте или утилизации.
    """
    # Проверяем, существует ли уже запись в базе
    if instance.pk:
        try:
            old_instance = Equipment.objects.get(pk=instance.pk)
            old_status = old_instance.status

            # Если статус изменился на "Требуется ремонт"
            if old_status != 'NEEDS_REPAIR' and instance.status == 'NEEDS_REPAIR':
                # Проверяем, есть ли уже запись о ремонте
                if not hasattr(instance, 'repair_record'):
                    # Создаем запись о ремонте после сохранения
                    instance._need_repair_record = True

            # Если статус изменился на "Утилизировано"
            elif old_status != 'DISPOSED' and instance.status == 'DISPOSED':
                # Проверяем, есть ли уже запись об утилизации
                if not hasattr(instance, 'disposal_record'):
                    # Создаем запись об утилизации после сохранения
                    instance._need_disposal_record = True

        except Equipment.DoesNotExist:
            # Объект ещё не существует
            pass

@receiver(post_save, sender=Equipment)
def create_maintenance_records(sender, instance, created, **kwargs):
    """
    Сигнал для создания записей о ремонте или утилизации после сохранения оборудования.
    """
    # Если нужно создать запись о ремонте
    if hasattr(instance, '_need_repair_record') and instance._need_repair_record:
        Repair.objects.create(
            equipment=instance,
            notes=f"Автоматически создано при изменении статуса оборудования на 'Требуется ремонт'."
        )
        # Удаляем временный флаг
        delattr(instance, '_need_repair_record')

    # Если нужно создать запись об утилизации
    if hasattr(instance, '_need_disposal_record') and instance._need_disposal_record:
        Disposal.objects.create(
            equipment=instance,
            reason="Автоматически создано при изменении статуса оборудования на 'Утилизировано'.",
            notes="Запись создана системой."
        )
        # Удаляем временный флаг
        delattr(instance, '_need_disposal_record')