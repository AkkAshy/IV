from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter



router = DefaultRouter()
router.register(r'room', views.RoomViewSet, basename='room')
router.register(r'faculties', views.FacultyViewSet, basename='faculty')



urlpatterns = [

    path('api/', include(router.urls)),

    # Университеты
    path('', views.UniversityListCreateView.as_view(), name='university-list-create'),
    path('<int:pk>/', views.UniversityDetailView.as_view(), name='university-detail'),

    # Корпуса
    path('buildings/', views.BuildingListCreateView.as_view(), name='building-list-create'),
    path('buildings/<int:pk>/', views.BuildingDetailView.as_view(), name='building-detail'),

    # Факультеты
    path('faculties/', views.FacultyListCreateView.as_view(), name='faculty-list-create'),
    path('faculties/<int:pk>/', views.FacultyDetailView.as_view(), name='faculty-detail'),

    # Этажи
    path('floors/', views.FloorListCreateView.as_view(), name='floor-list-create'),
    path('floors/<int:pk>/', views.FloorDetailView.as_view(), name='floor-detail'),
    path('buildings/<int:building_pk>/floors/', views.FloorByBuildingView.as_view()),

    # Кабинеты
    path('rooms/', views.RoomListCreateView.as_view(), name='room-list-create'),
    path('rooms/<int:pk>/', views.RoomDetailView.as_view(), name='room-detail'),

    # Кабинеты по корпусу
    path('rooms_in_building/', views.RoomListByBuildingView.as_view(), name='get_rooms_by_building'),

    path('rooms/<int:pk>/link/', views.RoomLinkView.as_view(), name='room-link'),

    path('edit/', include(router.urls)),
]