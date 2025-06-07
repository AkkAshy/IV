# inventory/permissions.py
from rest_framework import permissions

class IsAdminOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        # Все авторизованные пользователи могут видеть или создавать
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Администраторы могут делать всё
        if request.user.is_staff or request.user.is_superuser:
            return True
        # Обычные пользователи могут взаимодействовать только со своими контрактами
        return obj.author == request.user