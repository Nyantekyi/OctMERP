"""
config/routing.py — WebSocket URL patterns for Django Channels.
"""

from django.urls import path

websocket_urlpatterns = [
    # Dashboard live feed
    path("ws/dashboard/", lambda: None),   # placeholder — replace with actual consumer
    # POS live session
    path("ws/pos/<str:session_id>/", lambda: None),
    # Agent activity feed
    path("ws/agents/<str:agent_id>/", lambda: None),
    # Notifications
    path("ws/notifications/", lambda: None),
]
