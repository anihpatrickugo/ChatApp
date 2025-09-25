
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied

from .models import User, FriendRequest, ChatRoom, ChatMessage
from .serializers import (
    PrivateChatRoomSerializer,
    GroupChatRoomSerializer,
    FriendRequestSerializer,
    ChatMessageSerializer,
    UserSerializer,
)

# ------------------ FRIEND REQUEST VIEWS ------------------

class FriendRequestListView(generics.ListAPIView):
    """
    Lists all friend requests received by the logged-in user,
    including sender details.
    """
    serializer_class = FriendRequestSerializer


    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user)


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

class PrivateChatRoomListView(generics.ListAPIView):
    """List all rooms where the authenticated user is a participant"""
    serializer_class = PrivateChatRoomSerializer

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(participants=user).order_by("-created_at")


class GroupRoomListView(generics.ListAPIView):
    """List all rooms where the authenticated user is a participant"""
    serializer_class = GroupChatRoomSerializer

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(participants=user).order_by("-created_at")


class ChatRoomFriendView(APIView):


    def get(self, request, room_id):

        room = get_object_or_404(ChatRoom, pk=room_id)

        # Ensure the current user is a participant
        if request.user not in room.participants.all():
            return JsonResponse({"error": "You are not part of this room"}, status=403)

        # Find the other participant
        friend = room.participants.exclude(id=request.user.id).first()

        if not friend:
            return JsonResponse({"error": "No friend found"}, status=404)

        # Return friend details (with photo)
        return JsonResponse({
            "id": friend.id,
            "username": friend.username,
            "first_name": friend.first_name,
            "last_name": friend.last_name,
            "email": friend.email,
            "photo_url": request.build_absolute_uri(friend.photo.url) if friend.photo else None,
        })


class ChatMessageListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        room_id = self.kwargs["room_id"]

        # ✅ Check if user is participant in the room
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            raise PermissionDenied("This room does not exist.")

        if not room.participants.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a participant in this room.")

        # ✅ Return only this room's messages
        return ChatMessage.objects.filter(room=room).order_by("timestamp")



class EditProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


