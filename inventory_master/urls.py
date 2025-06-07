# project/urls.py
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)




urlpatterns = [
    path('custom_admin/', include('custom_admin.urls')),
    path('admin/', admin.site.urls),  # Стандартная Django-админка
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', include('user.urls')),
    path('university/', include('university.urls')),
    path('inventory/', include('inventory.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)