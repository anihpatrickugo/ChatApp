

from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import User, ChatMessage

class CustomRegisterSerializer(RegisterSerializer):
    _has_phone_field = False  # Add this line

    # Add any extra fields you need here, e.g., 'first_name', 'last_name'
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    def custom_signup(self, request, user):
        user.first_name = self.validated_data.get('first_name', '')
        user.last_name = self.validated_data.get('last_name', '')
        user.save(update_fields=['first_name', 'last_name'])



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'receiver', 'message', 'timestamp']