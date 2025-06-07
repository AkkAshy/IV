from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # Университеты
    path('universities/', views.UniversityListView.as_view(), name='university_list'),
    path('universities/create/', views.UniversityCreateView.as_view(), name='university_create'),
    path('universities/<int:pk>/edit/', views.UniversityUpdateView.as_view(), name='university_edit'),
    path('universities/<int:pk>/delete/', views.UniversityDeleteView.as_view(), name='university_delete'),
    # Корпуса
    path('buildings/', views.BuildingListView.as_view(), name='building_list'),
    path('buildings/create/', views.BuildingCreateView.as_view(), name='building_create'),
    path('buildings/<int:pk>/edit/', views.BuildingUpdateView.as_view(), name='building_edit'),
    path('buildings/<int:pk>/delete/', views.BuildingDeleteView.as_view(), name='building_delete'),
    # Факультеты
    path('faculties/', views.FacultyListView.as_view(), name='faculty_list'),
    path('faculties/create/', views.FacultyCreateView.as_view(), name='faculty_create'),
    path('faculties/<int:pk>/edit/', views.FacultyUpdateView.as_view(), name='faculty_edit'),
    path('faculties/<int:pk>/delete/', views.FacultyDeleteView.as_view(), name='faculty_delete'),
    # Этажи
    path('floors/', views.FloorListView.as_view(), name='floor_list'),
    path('floors/create/', views.FloorCreateView.as_view(), name='floor_create'),
    path('floors/<int:pk>/edit/', views.FloorUpdateView.as_view(), name='floor_edit'),
    path('floors/<int:pk>/delete/', views.FloorDeleteView.as_view(), name='floor_delete'),
    # Кабинеты
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/create/', views.RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/edit/', views.RoomUpdateView.as_view(), name='room_edit'),
    path('rooms/<int:pk>/delete/', views.RoomDeleteView.as_view(), name='room_delete'),
    # Оборудование
    path('equipment/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='equipment_edit'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment_delete'),
    # Договоры
    path('contracts/', views.ContractDocumentListView.as_view(), name='contract_document_list'),
    path('contracts/create/', views.ContractDocumentCreateView.as_view(), name='contract_document_create'),
    path('contracts/<int:pk>/edit/', views.ContractDocumentUpdateView.as_view(), name='contract_document_edit'),
    path('contracts/<int:pk>/delete/', views.ContractDocumentDeleteView.as_view(), name='contract_document_delete'),
    # Пользователи
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    # Перемещения
    path('movements/', views.MovementListView.as_view(), name='movement_list'),
    path('movements/create/', views.MovementCreateView.as_view(), name='movement_create'),
    path('movements/<int:pk>/edit/', views.MovementUpdateView.as_view(), name='movement_edit'),
    path('movements/<int:pk>/delete/', views.MovementDeleteView.as_view(), name='movement_delete'),
       # Типы оборудования
    path('equipment-types/', views.EquipmentTypeListView.as_view(), name='equipment_type_list'),
    path('equipment-types/create/', views.EquipmentTypeCreateView.as_view(), name='equipment_type_create'),
    path('equipment-types/<int:pk>/edit/', views.EquipmentTypeUpdateView.as_view(), name='equipment_type_edit'),
    path('equipment-types/<int:pk>/delete/', views.EquipmentTypeDeleteView.as_view(), name='equipment_type_delete'),

    path('load-floors/', views.load_floors, name='load_floors'),
    path('ajax/load-floors/', views.load_floors, name='ajax_load_floors'),
]