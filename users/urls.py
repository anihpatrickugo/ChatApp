from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    FriendRequestListView,
    FriendRequestSendView,
    FriendRequestAcceptView,
    FriendRequestDeclineView,


    PrivateChatRoomListView,
    GroupRoomListView,

    ChatRoomFriendView,
    ChatMessageListView,
    EditProfileView
)

urlpatterns = [
    # --- Authentication ---
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/user/profile/', EditProfileView.as_view(), name='edit_profile'),

    # --- Friend Requests ---
    path('list-request/', FriendRequestListView.as_view(), name='list-request'),
    path('send-request/<int:user_id>/', FriendRequestSendView.as_view(), name='send-request'),
    path('accept-request/<int:request_id>/', FriendRequestAcceptView.as_view(), name='accept-request'),
    path('decline-request/<int:request_id>/', FriendRequestDeclineView.as_view(), name='decline-request'),

    # --- Chat (Option B: Room-based) ---
    path("chat-list/", PrivateChatRoomListView.as_view(), name="chatroom-list"),
    path("group-list/", GroupRoomListView.as_view(), name="group-list"),

    path("chatroom/<int:room_id>/friend/", ChatRoomFriendView.as_view(), name="chatroom-friend"),
    path("chatroom/<int:room_id>/messages/", ChatMessageListView.as_view(), name="chat-messages"),

]
