from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # rota dinâmica que recebe o ID do grupo
    path('ws/notificacao-feed/', consumers.AlertaFeedConsumer.as_asgi()),
    path('ws/chat/<int:grupo_id>/', consumers.ChatConsumer.as_asgi()),
]
