from django.test import TestCase
from lobby.models import Avaliacao, Jogo
from django.urls import reverse
from django.contrib.auth.models import User

class JogoTestCase(TestCase):
    def test_nao_duplicar_jogo(self):
        # Cria o jogo
        Jogo.objects.create(titulo="Hollow Knight", genero="Ação e Aventura", plataforma="PC")
        
        # Tenta cadastrar de novo via POST
        response = self.client.post(reverse('add_game'), {
            'titulo': 'Hollow Knight',
            'genero': 'Ação e Aventura', 
            'plataforma': 'PS5'
        })
        
        # Verifica se continua com apenas 1
        self.assertEqual(Jogo.objects.count(), 1)

class AvaliacaoTestCase(TestCase):
    def setUp(self):
        # O método setUp roda antes de cada teste para preparar o "terreno"
        self.usuario_autor = User.objects.create_user(username='autor', password='123')
        self.usuario_invasor = User.objects.create_user(username='invasor', password='123')
        
        self.jogo = Jogo.objects.create(titulo="Resident Evil 5", genero="Ação", plataforma="PC")
        
        self.avaliacao = Avaliacao.objects.create(
            jogo=self.jogo,
            usuario=self.usuario_autor,
            nota=9.0,
            comentario="Wesker."
        )

    def test_invasor_nao_pode_apagar_avaliacao(self):
        # Fazemos login com o usuário invasor
        self.client.login(username='invasor', password='123')
        
        # Ele manda o POST para deletar a review do outro usuário
        response = self.client.post(reverse('deletar_avaliacao', args=[self.avaliacao.id]))
        
        #C Verifica se o invasor não conseguiu apagar a review
        self.assertEqual(Avaliacao.objects.count(), 1)

    def test_autor_pode_apagar_avaliacao(self):
        #Fazemos login com o verdadeiro dono da review
        self.client.login(username='autor', password='123')
        
        # Ele manda o POST para deletar a própria review
        response = self.client.post(reverse('deletar_avaliacao', args=[self.avaliacao.id]))
        
        # Verificamos se apagou com sucesso
        self.assertEqual(Avaliacao.objects.count(), 0)
