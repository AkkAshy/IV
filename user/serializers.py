from rest_framework import serializers
from .models import User, SupportMessage, UserAction

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)
    full_name = serializers.SerializerMethodField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'profile_picture', 'role', 'role_display', 
            'is_active', 'date_joined', 'last_login', 'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'full_name', 'role_display']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate(self, data):
        # Проверка паролей при создании или изменении
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        
        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError("Пароли не совпадают.")
            
            if len(password) < 6:
                raise serializers.ValidationError("Пароль должен содержать минимум 6 символов.")
        
        return data

    def create(self, validated_data):
        # Удаляем password_confirm из данных
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        # Создаем пользователя
        user = User.objects.create(**validated_data)
        
        # Устанавливаем пароль, если он был передан
        if password:
            user.set_password(password)
            user.save()
        
        return user

    def update(self, instance, validated_data):
        # Удаляем password_confirm из данных
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        # Обновляем поля пользователя
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Обновляем пароль, если он был передан
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserDetailSerializer(UserSerializer):
    """
    Расширенный сериализатор для админов с дополнительной информацией
    """
    groups = serializers.StringRelatedField(many=True, read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'is_staff', 'is_superuser', 'groups'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Специальный сериализатор для создания пользователей
    """
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'role', 'password', 'password_confirm'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления информации пользователя
    """
    password = serializers.CharField(write_only=True, required=False, min_length=6)
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'email',
            'profile_picture', 'password', 'password_confirm'
        ]

    def validate(self, data):
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        
        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError("Пароли не совпадают.")
        
        return data

    def update(self, instance, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


# Остальные сериализаторы остаются без изменений
class SupportMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = ['id', 'sender', 'subject', 'message', 'sent_at', 'is_resolved']
        read_only_fields = ['id', 'sender', 'sent_at', 'is_resolved']


class UserActionSerializer(serializers.ModelSerializer):
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    content_object_display = serializers.SerializerMethodField()

    class Meta:
        model = UserAction
        fields = [
            'id', 'user', 'action_type', 'action_type_display', 'description',
            'created_at', 'content_type', 'object_id', 'content_object_display',
            'old_value', 'new_value', 'details'
        ]
        read_only_fields = [
            'id', 'user', 'action_type', 'action_type_display', 'description',
            'created_at', 'content_type', 'object_id', 'content_object_display',
            'old_value', 'new_value', 'details'
        ]

    def get_content_object_display(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return "N/A"