# Обновить user/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from .models import User, SupportMessage
from .serializers import UserSerializer, SupportMessageSerializer
from .permissions import IsAdminUser

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Настройка прав доступа для разных действий
        """
        if self.action in ['list', 'create', 'destroy', 'update', 'partial_update']:
            # Только админы могут просматривать список всех пользователей, создавать, удалять и редактировать других
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ['retrieve']:
            # Просмотр конкретного пользователя: админ может всех, обычный пользователь - только себя
            permission_classes = [IsAuthenticated]
        else:
            # Для кастомных действий используем базовые права
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]

    def retrieve(self, request, *args, **kwargs):
        """
        Получение информации о пользователе по ID
        Админ может получить любого пользователя, обычный пользователь - только себя
        """
        user = self.get_object()
        
        # Если пользователь не админ и пытается получить не свою информацию
        if not request.user.is_admin() and user.id != request.user.id:
            raise PermissionDenied("Вы можете просматривать только свою информацию.")
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Обновление информации пользователя
        Админ может редактировать любого, обычный пользователь - только себя
        """
        user = self.get_object()
        
        # Если пользователь не админ и пытается редактировать не себя
        if not request.user.is_admin() and user.id != request.user.id:
            raise PermissionDenied("Вы можете редактировать только свою информацию.")
        
        # Если обычный пользователь пытается изменить роль
        if not request.user.is_admin() and 'role' in request.data:
            raise PermissionDenied("Вы не можете изменять роль.")
        
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Частичное обновление информации пользователя
        """
        user = self.get_object()
        
        # Если пользователь не админ и пытается редактировать не себя
        if not request.user.is_admin() and user.id != request.user.id:
            raise PermissionDenied("Вы можете редактировать только свою информацию.")
        
        # Если обычный пользователь пытается изменить роль
        if not request.user.is_admin() and 'role' in request.data:
            raise PermissionDenied("Вы не можете изменять роль.")
        
        return super().partial_update(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Создание нового пользователя (только для админов)
        """
        if not self.request.user.is_admin():
            raise PermissionDenied("Только администратор может создавать пользователей.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """
        Удаление пользователя (только для админов)
        """
        if not request.user.is_admin():
            raise PermissionDenied("Только администратор может удалять пользователей.")
        
        user = self.get_object()
        
        # Запретить удаление самого себя
        if user.id == request.user.id:
            raise PermissionDenied("Вы не можете удалить свой собственный аккаунт.")
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Получение информации о текущем пользователе по токену
        GET /api/users/user/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch', 'put'], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        """
        Обновление информации текущего пользователя
        PATCH/PUT /api/users/user/update_me/
        """
        # Запретить изменение роли обычным пользователям
        if not request.user.is_admin() and 'role' in request.data:
            raise PermissionDenied("Вы не можете изменять роль.")
        
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def admin_detail(self, request, pk=None):
        """
        Получение подробной информации о пользователе для админа
        GET /api/users/user/{id}/admin_detail/
        """
        user = get_object_or_404(User, pk=pk)
        serializer = self.get_serializer(user)
        
        # Дополнительная информация для админа
        data = serializer.data
        data.update({
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'groups': [group.name for group in user.groups.all()],
        })
        
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def toggle_active(self, request, pk=None):
        """
        Активация/деактивация пользователя
        POST /api/users/user/{id}/toggle_active/
        """
        user = get_object_or_404(User, pk=pk)
        
        # Запретить деактивацию самого себя
        if user.id == request.user.id:
            raise PermissionDenied("Вы не можете деактивировать свой собственный аккаунт.")
        
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'id': user.id,
            'username': user.username,
            'is_active': user.is_active,
            'message': f"Пользователь {'активирован' if user.is_active else 'деактивирован'}"
        })

# Остальные классы остаются без изменений
class SupportMessageCreateAPIView(generics.CreateAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class SupportMessageListAPIView(generics.ListAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [IsAdminUser]
    queryset = SupportMessage.objects.all().order_by('-sent_at')


class NewSupportMessagesAPIView(generics.ListAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return SupportMessage.objects.filter(is_notified=False).order_by('-sent_at')


class MarkSupportMessageAsNotifiedAPIView(generics.UpdateAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [IsAdminUser]
    queryset = SupportMessage.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_notified = True
        instance.save()
        return Response({'status': 'marked as notified'})