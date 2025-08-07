from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FriendRequest, ChatMessage

# Register your custom User model with the admin site.
# This allows you to manage users and their friends directly from the
# Django admin panel.
admin.site.register(User)

# Register the new FriendRequest model.
# admin.site.register(FriendRequest)

# Register the new ChatMessage model.
admin.site.register(ChatMessage)