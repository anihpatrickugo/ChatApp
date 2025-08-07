import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Import your routing configuration.
from users.routing import websocket_urlpatterns

from .middleware import JWTAuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # New: Add a WebSocket protocol type.
    "websocket": AuthMiddlewareStack(
        JWTAuthMiddlewareStack(URLRouter(
            websocket_urlpatterns
        ))
    ),
})