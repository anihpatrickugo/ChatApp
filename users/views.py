from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from .models import User, FriendRequest, ChatRoom, ChatMessage
from .serializers import ChatMessageSerializer



# ------------------ FRIEND REQUEST VIEWS ------------------

class FriendRequestSendView(APIView):
    def post(self, request, user_id):
        to_user = get_object_or_404(User, id=user_id)
        from_user = request.user

        if from_user == to_user:
            return Response({"error": "You cannot send a friend request to yourself."},
                            status=status.HTTP_400_BAD_REQUEST)

        if FriendRequest.objects.filter(
            Q(from_user=from_user, to_user=to_user) |
            Q(from_user=to_user, to_user=from_user)
        ).exists():
            return Response({"error": "A friend request already exists."}, status=status.HTTP_409_CONFLICT)

        if from_user.friends.filter(id=to_user.id).exists():
            return Response({"error": "You are already friends."}, status=status.HTTP_409_CONFLICT)

        FriendRequest.objects.create(from_user=from_user, to_user=to_user)
        return Response({"message": f"Friend request sent to {to_user.username}."},
                        status=status.HTTP_201_CREATED)


class FriendRequestAcceptView(APIView):
    def post(self, request, request_id):
        friend_request = get_object_or_404(FriendRequest, id=request_id)

        if request.user != friend_request.to_user:
            return Response({"error": "You are not authorized to accept this request."},
                            status=status.HTTP_403_FORBIDDEN)

        # Add both users as friends
        friend_request.from_user.friends.add(friend_request.to_user)
        friend_request.to_user.friends.add(friend_request.from_user)

        # Create a chat room if one doesn’t already exist
        room, created = ChatRoom.objects.get_or_create()
        room.participants.add(friend_request.from_user, friend_request.to_user)

        friend_request.delete()

        return Response({"message": f"You are now friends with {friend_request.from_user.username}!"},
                        status=status.HTTP_200_OK)


class FriendRequestDeclineView(APIView):
    def post(self, request, request_id):
        friend_request = get_object_or_404(FriendRequest, id=request_id)

        if request.user != friend_request.to_user:
            return Response({"error": "You are not authorized to decline this request."},
                            status=status.HTTP_403_FORBIDDEN)

        friend_request.delete()
        return Response({"message": "Friend request declined."}, status=status.HTTP_200_OK)


# ------------------ CHAT VIEWS ------------------

# Fetch all messages in a specific chat room
class ChatRoomMessagesListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        current_user = self.request.user

        room = get_object_or_404(ChatRoom, id=room_id)

        # Ensure the current user is a participant
        if not room.participants.filter(id=current_user.id).exists():
            return ChatMessage.objects.none()

        return room.messages.all().order_by("timestamp")


# Optional: send a new message into a room
class ChatRoomSendMessageView(APIView):
    def post(self, request, room_id):
        room = get_object_or_404(ChatRoom, id=room_id)
        current_user = request.user

        if not room.participants.filter(id=current_user.id).exists():
            return Response(
                {"error": "You are not part of this chat room."},
                status=status.HTTP_403_FORBIDDEN
            )

        message_text = request.data.get("message")
        if not message_text:
            return Response(
                {"error": "Message cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save to DB
        msg = ChatMessage.objects.create(
            room=room,
            sender=current_user,
            message=message_text
        )

        serializer = ChatMessageSerializer(msg)

        # Broadcast to WebSocket group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room.id}",
            {
                "type": "chat.message",
                "room_id": room.id,
                "user": current_user.username,
                "message": serializer.data["message"],
                "timestamp": serializer.data["timestamp"],
            }
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)