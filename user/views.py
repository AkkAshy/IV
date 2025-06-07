from rest_framework import viewsets

from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer, SupportMessageSerializer

from .permissions import IsAdminUser  # Импортируем кастомный пермишн
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions
from .models import SupportMessage

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        if not self.request.user.is_admin():
            raise PermissionDenied("Только администратор может создавать пользователей.")
        serializer.save()

    # Этот метод будет отвечать за логику аутентификации
    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Возвращаем успешную авторизацию или токен, если пользователь авторизован
            return super().create(request, *args, **kwargs)
        return Response({"detail": "Unauthorized"}, status=401)



class SupportMessageCreateAPIView(generics.CreateAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class SupportMessageListAPIView(generics.ListAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SupportMessage.objects.all().order_by('-sent_at')



class NewSupportMessagesAPIView(generics.ListAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return SupportMessage.objects.filter(is_notified=False).order_by('-sent_at')



class MarkSupportMessageAsNotifiedAPIView(generics.UpdateAPIView):
    serializer_class = SupportMessageSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SupportMessage.objects.all()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_notified = True
        instance.save()
        return Response({'status': 'marked as notified'})
