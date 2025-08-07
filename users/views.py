from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import User, FriendRequest, ChatMessage
from .serializers import  ChatMessageSerializer


# This class-based view handles sending a friend request.
class FriendRequestSendView(APIView):

    def post(self, request, user_id):
        # Get the user to whom the request is being sent.
        to_user = get_object_or_404(User, id=user_id)

        # Get the currently logged-in user (the sender).
        from_user = request.user

        # Prevent a user from sending a request to themselves.
        if from_user == to_user:
            return Response({"error": "You cannot send a friend request to yourself."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if a request already exists between the users.
        if FriendRequest.objects.filter(
                Q(from_user=from_user, to_user=to_user) | Q(from_user=to_user, to_user=from_user)
        ).exists():
            return Response({"error": "A friend request already exists."}, status=status.HTTP_409_CONFLICT)

        # Check if they are already friends.
        if from_user.friends.filter(id=to_user.id).exists():
            return Response({"error": "You are already friends with this user."}, status=status.HTTP_409_CONFLICT)

        # Create the new friend request.
        FriendRequest.objects.create(from_user=from_user, to_user=to_user)

        return Response({"message": f"Friend request sent to {to_user.username}!"}, status=status.HTTP_201_CREATED)


# This class-based view handles accepting a friend request.
class FriendRequestAcceptView(APIView):

    def post(self, request, request_id):
        # Get the friend request object.
        friend_request = get_object_or_404(FriendRequest, id=request_id)

        # Only the recipient can accept the request.
        if request.user != friend_request.to_user:
            return Response({"error": "You are not authorized to accept this request."},
                            status=status.HTTP_403_FORBIDDEN)

        # Add both users to each other's friends list.
        friend_request.from_user.friends.add(friend_request.to_user)
        friend_request.to_user.friends.add(friend_request.from_user)

        # Delete the request object after it's been accepted.
        friend_request.delete()

        return Response({"message": f"You are now friends with {friend_request.from_user.username}!"},
                        status=status.HTTP_200_OK)


# This class-based view handles declining a friend request.
class FriendRequestDeclineView(APIView):

    def post(self, request, request_id):
        # Get the friend request object.
        friend_request = get_object_or_404(FriendRequest, id=request_id)

        # Only the recipient can decline the request.
        if request.user != friend_request.to_user:
            return Response({"error": "You are not authorized to decline this request."},
                            status=status.HTTP_403_FORBIDDEN)

        # Simply delete the request.
        friend_request.delete()

        return Response({"message": "Friend request declined."}, status=status.HTTP_200_OK)


# New: A class-based view to list chat messages between two users.
class ChatMessagesListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer


    def get_queryset(self):
        # Get the friend's ID from the URL.
        friend_id = self.kwargs['friend_id']
        current_user = self.request.user

        # Ensure the users are friends before fetching messages.
        if not current_user.friends.filter(id=friend_id).exists():
            return ChatMessage.objects.none()  # Return an empty queryset.

        # Fetch messages where the sender is the current user and the receiver is the friend,
        # OR the sender is the friend and the receiver is the current user.
        queryset = ChatMessage.objects.filter(
            Q(sender=current_user, receiver__id=friend_id) |
            Q(sender__id=friend_id, receiver=current_user)
        ).order_by('timestamp')

        return queryset