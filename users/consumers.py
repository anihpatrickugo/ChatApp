import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

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

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "room_id": event["room_id"],
            "user": event["user"],
            "message": event["message"],
            "timestamp": event["timestamp"],
        }))

    @database_sync_to_async
    def get_user_rooms(self, user):
        return list(user.chatrooms.values_list("id", flat=True))
