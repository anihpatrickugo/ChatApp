from django.db import models
from django.contrib.auth.models import AbstractUser


# Create a custom user model that inherits from Django's AbstractUser.
# This gives you all the standard user fields (username, password, email, etc.)
# and allows you to add new ones.
class User(AbstractUser):
    photo = models.ImageField(upload_to="photo/", null=True, blank=True)
    friends = models.ManyToManyField(
        'self',
        symmetrical=True,
        blank=True
    )

    def __str__(self):
        return self.username


# This is the new model for tracking friend requests.
class FriendRequest(models.Model):
    # 'from_user' is the user who sends the request.
    from_user = models.ForeignKey(User, related_name='from_user', on_delete=models.CASCADE)

    # 'to_user' is the user who receives the request.
    to_user = models.ForeignKey(User, related_name='to_user', on_delete=models.CASCADE)

    # 'timestamp' records when the request was created.
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request from {self.from_user.username} to {self.to_user.username}"

    class Meta:
        # Ensures that a user can only send one friend request to another user.
        unique_together = ('from_user', 'to_user')


class ChatRoom(models.Model):
    participants = models.ManyToManyField(User, related_name="chatrooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.id} ({', '.join([u.username for u in self.participants.all()])})"


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.room.id}] {self.sender.username}: {self.message[:20]}"
