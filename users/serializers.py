

from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import User, ChatMessage, ChatRoom, FriendRequest

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
        fields = ["id", "username", "email", "first_name", "last_name", "photo"]




class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.username")  # show username instead of ID
    room = serializers.IntegerField(source="room.id")

    class Meta:
        model = ChatMessage
        fields = ["id", "room", "sender", "message", "timestamp"]


class PrivateChatRoomSerializer(serializers.ModelSerializer):
    # Show only the other participant(s), excluding current user
    participants = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ["id", "participants", "created_at", "last_message"]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-timestamp").first()
        if last:
            return ChatMessageSerializer(last).data
        return None

    def get_participants(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        others = obj.participants.exclude(id=user.id) if user else obj.participants.all()
        return UserSerializer(others, many=True, context={"request": request}).data



class GroupChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ["id", "participants", "created_at"]


class FriendRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ["id", "from_user", "timestamp"]