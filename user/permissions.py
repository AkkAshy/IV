from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Разрешение для доступа только для администраторов.
    """

    def has_permission(self, request, view):
        # Проверяем, является ли пользователь администратором
        return request.user and request.user.is_admin()
