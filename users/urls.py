
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import FriendRequestSendView, FriendRequestAcceptView, FriendRequestDeclineView, ChatMessagesListView

urlpatterns = [
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('send-request/<int:user_id>/', FriendRequestSendView.as_view(), name='send-request'),
    path('accept-request/<int:request_id>/', FriendRequestAcceptView.as_view(), name='accept-request'),
    path('decline-request/<int:request_id>/', FriendRequestDeclineView.as_view(), name='decline-request'),
    path('api/chat-messages/<int:friend_id>/', ChatMessagesListView.as_view(), name='chat-messages-list'),
]