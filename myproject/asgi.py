import os
import django
from django.core.asgi import get_asgi_application

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django.setup(set_prefix=False)
django_asgi_app = get_asgi_application()

# Now import Channels components after Django is initialized
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Import WebSocket routes (must be after Django setup)
try:
    import authentication.routing
except ImportError:
    # Fallback if websocket routes aren't available
    websocket_routes = []
else:
    websocket_routes = authentication.routing.websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_routes)
    ),
})