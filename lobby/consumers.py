import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Grupo, MensagemGrupo

class AlertaFeedConsumer(WebsocketConsumer):
    def connect(self):
        self.nome_da_sala = 'feed_global_notificacoes'

        # Inscreve o usuário para ouvir os alarmes
        async_to_sync(self.channel_layer.group_add)(
            self.nome_da_sala,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.nome_da_sala,
            self.channel_name
        )

    def disparar_alerta(self, event):
        # Manda um sinal vazio para o JavaScript saber que algo aconteceu
        self.send(text_data=json.dumps({
            'alerta': 'tem_post_novo'
        }))

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.grupo_id = self.scope['url_route']['kwargs']['grupo_id']
        self.nome_da_sala = f'chat_grupo_{self.grupo_id}'

        async_to_sync(self.channel_layer.group_add)(
            self.nome_da_sala,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.nome_da_sala,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        mensagem = text_data_json['mensagem']
        usuario = self.scope['user'] # Pega o objeto do usuário logado

        grupo_obj = Grupo.objects.get(id=self.grupo_id)
        MensagemGrupo.objects.create(
            grupo=grupo_obj,
            usuario=usuario,
            texto=mensagem
        )


        async_to_sync(self.channel_layer.group_send)(
            self.nome_da_sala,
            {
                'type': 'chat_message',
                'mensagem': mensagem,
                'usuario': usuario.username
            }
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'mensagem': event['mensagem'],
            'usuario': event['usuario']
        }))