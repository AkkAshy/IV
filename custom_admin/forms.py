from django import forms
from django.contrib.auth.forms import UserCreationForm
from inventory.models import Equipment, ContractDocument, EquipmentType, ComputerDetails, MovementHistory
from university.models import University, Building, Faculty, Floor, Room
from user.models import User
from django.utils import timezone




class EquipmentForm(forms.ModelForm):
    cpu = forms.CharField(max_length=255, required=False, label='Процессор', widget=forms.TextInput(attrs={'class': 'form-control computer-field'}))
    ram = forms.CharField(max_length=255, required=False, label='Оперативная память', widget=forms.TextInput(attrs={'class': 'form-control computer-field'}))
    storage = forms.CharField(max_length=255, required=False, label='Накопитель', widget=forms.TextInput(attrs={'class': 'form-control computer-field'}))
    has_keyboard = forms.BooleanField(required=False, label='Есть ли клавиатура', widget=forms.CheckboxInput(attrs={'class': 'form-check-input computer-field'}))
    has_mouse = forms.BooleanField(required=False, label='Есть ли мышь', widget=forms.CheckboxInput(attrs={'class': 'form-check-input computer-field'}))
    monitor_size = forms.CharField(max_length=50, required=False, label='Размер монитора', widget=forms.TextInput(attrs={'class': 'form-control computer-field'}))

    class Meta:
        model = Equipment
        fields = ['type', 'room', 'name', 'photo', 'description', 'is_active', 'inn', 'contract']
        labels = {
            'type': 'Тип оборудования',
            'room': 'Кабинет',
            'name': 'Название оборудования',
            'photo': 'Фото оборудования',
            'description': 'Описание',
            'is_active': 'Активно',
            'inn': 'ИНН',
            'contract': 'Договор',
        }
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control', 'id': 'id_type'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'inn': forms.TextInput(attrs={'class': 'form-control'}),
            'contract': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        print(f"EquipmentForm init: args={args}, kwargs={kwargs}")
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and hasattr(self.instance, 'computer_details') and self.instance.computer_details:
            try:
                computer_details = self.instance.computer_details
                print(f"Found computer_details: {computer_details}")
                self.fields['cpu'].initial = computer_details.cpu
                self.fields['ram'].initial = computer_details.ram
                self.fields['storage'].initial = computer_details.storage
                self.fields['has_keyboard'].initial = computer_details.has_keyboard
                self.fields['has_mouse'].initial = computer_details.has_mouse
                self.fields['monitor_size'].initial = computer_details.monitor_size
            except Exception as e:
                print(f"Error accessing computer_details: {e}")

    def clean(self):
        cleaned_data = super().clean()
        print(f"EquipmentForm clean: cleaned_data={cleaned_data}")
        return cleaned_data

    def save(self, commit=True):
        print(f"EquipmentForm save: cleaned_data={self.cleaned_data}")
        equipment = super().save(commit=False)
        print(f"Saving equipment: {equipment}")
        if commit:
            try:
                equipment.save()
                print("Equipment saved successfully")
                if any(self.cleaned_data.get(field) for field in ['cpu', 'ram', 'storage', 'has_keyboard', 'has_mouse', 'monitor_size']):
                    print("Saving ComputerDetails")
                    computer_details, created = ComputerDetails.objects.get_or_create(equipment=equipment)
                    computer_details.cpu = self.cleaned_data['cpu']
                    computer_details.ram = self.cleaned_data['ram']
                    computer_details.storage = self.cleaned_data['storage']
                    computer_details.has_keyboard = self.cleaned_data['has_keyboard']
                    computer_details.has_mouse = self.cleaned_data['has_mouse']
                    computer_details.monitor_size = self.cleaned_data['monitor_size']
                    computer_details.save()
                    print("ComputerDetails saved successfully")
            except Exception as e:
                print(f"Error saving equipment or ComputerDetails: {e}")
                raise
        return equipment


# 📄 Договор
class ContractDocumentForm(forms.ModelForm):
    class Meta:
        model = ContractDocument
        fields = ['number', 'file', 'valid_until']

# 🎓 Университет
class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['name', 'address', 'logo']
        labels = {
            'name': 'Название университета',
            'address': 'Адрес',
            'logo': 'Логотип',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


# 🏢 Здание
class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['university', 'name', 'address', 'photo']
        labels = {
            'university': 'Университет',
            'name': 'Название корпуса',
            'address': 'Адрес корпуса',
            'photo': 'Фото корпуса',
        }
        widgets = {
            'university': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

# 🧪 Факультет
class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['building', 'floor', 'name', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Задаем пустой queryset для этажей по умолчанию
        self.fields['floor'].queryset = Floor.objects.none()

        # Если форма уже отправлена (POST запрос)
        if 'building' in self.data:
            try:
                building_id = int(self.data.get('building'))
                # Устанавливаем queryset для этажей выбранного корпуса
                self.fields['floor'].queryset = Floor.objects.filter(building_id=building_id)
            except (ValueError, TypeError):
                pass
        # Если это редактирование существующего объекта
        elif self.instance.pk and self.instance.building:
            # Устанавливаем queryset для этажей корпуса объекта
            self.fields['floor'].queryset = Floor.objects.filter(building=self.instance.building)

    def clean(self):
        cleaned_data = super().clean()
        building = cleaned_data.get('building')
        floor = cleaned_data.get('floor')

        # Проверяем, что выбранный этаж принадлежит выбранному корпусу
        if building and floor and floor.building != building:
            self.add_error('floor', 'Выбранный этаж не принадлежит выбранному корпусу')

        return cleaned_data

# 🪜 Этаж
class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['building', 'number', 'description']

# 🧭 Комната
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['floor', 'number', 'name', 'is_special', 'building', 'photo']
        labels = {
            'floor': 'Этаж',
            'number': 'Номер комнаты',
            'name': 'Название',
            'is_special': 'Особый кабинет',
            'building': 'Здание',
            'photo': 'Фото',
        }
        widgets = {
            'floor': forms.Select(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_special': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'building': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        building = cleaned_data.get('building')
        floor = cleaned_data.get('floor')
        if not building:
            raise forms.ValidationError("Пожалуйста, выберите здание.")
        if not floor:
            raise forms.ValidationError("Пожалуйста, выберите этаж.")
        return cleaned_data


# 👤 Пользователь
class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'phone_number', 'role',
            'profile_picture', 'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields.pop('password1')
            self.fields.pop('password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'role', 'profile_picture']


class MovementForm(forms.ModelForm):
    class Meta:
        model = MovementHistory
        fields = ['equipment', 'from_room', 'to_room', 'note']




    def clean(self):
        cleaned_data = super().clean()
        from_room = cleaned_data.get('from_room')
        to_room = cleaned_data.get('to_room')

        if from_room == to_room:
            raise forms.ValidationError("Комнаты 'откуда' и 'куда' не могут совпадать.")

        return cleaned_data

    def save(self, commit=True):
        movement = super().save(commit=False)
        equipment = movement.equipment

        # Обновляем текущую комнату оборудования
        equipment.room = movement.to_room
        if commit:
            equipment.save()
            movement.save()
        return movement


class EquipmentTypeForm(forms.ModelForm):
    class Meta:
        model = EquipmentType
        fields = ['name']
        labels = {
            'name': 'Название типа оборудования',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }