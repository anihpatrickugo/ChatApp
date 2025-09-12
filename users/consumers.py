import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage
from .serializers import ChatMessageSerializer

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        if user.is_anonymous:
            await self.close()
            return

        # join all chat rooms this user belongs to
        self.rooms = await self.get_user_rooms(user)
        for room_id in self.rooms:
            await self.channel_layer.group_add(f"chat_{room_id}", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        for room_id in getattr(self, "rooms", []):
            await self.channel_layer.group_discard(f"chat_{room_id}", self.channel_name)

    async def receive(self, text_data: str, bytes_data: bytes = None):
        """
        Expected JSON payload from client:
        {
            "room_id": 1,
            "message": "Hello World!"
        }
        """
        user = self.scope["user"]


        if not user.is_authenticated:
            return



        try:
            data = json.loads(text_data)
            room_id = data.get("room_id")
            message_text = data.get("message")

        except Exception:
            return

        if not room_id or not message_text:
            return

        # Save message in DB
        msg = await self.create_message(room_id, user, message_text)
        serializer = ChatMessageSerializer(msg)

        # Broadcast to room group
        await self.channel_layer.group_send(
            f"chat_{room_id}",
            {
                "type": "chat.message",
                "room_id": room_id,
                "user": user.username,
                "message": serializer.data["message"],
                "timestamp": serializer.data["timestamp"],
            }
        )

    async def chat_message(self, event):
        # Send to WebSocket
        await self.send(text_data=json.dumps(event))

    # ---------------- DB Helpers ----------------
    @database_sync_to_async
    def get_user_rooms(self, user):
        return list(user.chatrooms.values_list("id", flat=True))

    @database_sync_to_async
    def create_message(self, room_id, user, message):
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ObjectDoesNotExist:
            return None
        return ChatMessage.objects.create(room=room, sender=user, message=message)
