from rest_framework import serializers
from django.contrib.auth import authenticate
from user.models import User

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Неверные учетные данные')
        data['user'] = user
        return data