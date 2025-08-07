import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            # If the user is not logged in, reject the connection.
            await self.close()
            print("not authenticated")
            return

        # Get the other user's ID from the URL.
        self.friend_id = self.scope['url_route']['kwargs']['friend_id']
        self.friend = await sync_to_async(User.objects.get)(id=self.friend_id)

        # Ensure the two users are friends.
        if not await sync_to_async(self.user.friends.filter(id=self.friend.id).exists)():
            await self.close()
            print("not friends with this user")
            return

        # Create a unique group name for the chat.
        # This ensures both users are in the same chat room.
        user_ids = sorted([self.user.id, self.friend.id])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        # Join the chat group.
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the chat group.
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket.
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Save the message to the database.
        new_message = await sync_to_async(ChatMessage.objects.create)(
            sender=self.user,
            receiver=self.friend,
            message=message
        )

        # Send the message to the chat group.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'timestamp': str(new_message.timestamp)
            }
        )

    # Receive message from room group.
    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_username = event['sender_username']
        timestamp = event['timestamp']

        # Send message to WebSocket.
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'sender_username': sender_username,
            'timestamp': timestamp
        }))
