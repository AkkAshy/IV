from rest_framework import serializers
from .models import User, SupportMessage, UserAction

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'phone_number', 'email', 'profile_picture', 'role']


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