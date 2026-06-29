from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.core.cache import cache

GENERO_CHOICES = (
    ('Ação', 'Ação e Aventura'),
    ('Arcade', 'Arcade / Luta'),
    ('RPG', 'RPG / MMORPG'),
    ('FPS', 'Tiro em Primeira Pessoa (FPS)'),
    ('Esportes', 'Esportes / Corrida'),
    ('Estratégia', 'Estratégia / MOBA'),
)

PLATAFORMA_CHOICES = (
    ('PC', 'PC (Windows/Steam)'),
    ('PS5', 'PlayStation 5'),
    ('PS4', 'PlayStation 4'),
    ('Xbox Series', 'Xbox Series X/S'),
    ('Xbox One', 'Xbox One'),
    ('Switch', 'Nintendo Switch'),
    ('Mobile', 'Smartphone / Mobile'),
)

ESTILO_GRUPO_CHOICES = (
    ('Casual', 'Casual (Só por diversão)'),
    ('Competitivo', 'Competitivo (Tryhard/Ranked)'),
    ('Campanha', 'Foco em Missões / Campanha'),
    ('Iniciantes', 'Aceita Iniciantes (Mentoria)'),
)

   

class Jogo(models.Model):
    titulo = models.CharField(max_length=200)
    genero = models.CharField(max_length=50, choices=GENERO_CHOICES)
    plataforma = models.CharField(max_length=50, choices=PLATAFORMA_CHOICES)
    nota_media = models.FloatField(default=0.0)
    capa_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.titulo

class Avaliacao(models.Model):
    jogo = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.FloatField()
    comentario = models.TextField()
    data_publicacao = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)

        media = Avaliacao.objects.filter(jogo=self.jogo).aggregate(Avg('nota'))['nota__avg']

        self.jogo.nota_media = round(media, 1) if media else 0.0
        self.jogo.save()
        cache.delete('jogos_em_alta')
        cache.delete('estatisticas_home')

    def delete(self, *args, **kwargs):

        jogo_relacionado = self.jogo

        super().delete(*args, **kwargs)

        media = Avaliacao.objects.filter(jogo=jogo_relacionado).aggregate(Avg('nota'))['nota__avg']
        jogo_relacionado.nota_media = round(media, 1) if media else 0.0
        jogo_relacionado.save()
        cache.delete('jogos_em_alta')
        cache.delete('estatisticas_home')

    def __str__(self):
        return f"{self.usuario.username} - {self.jogo.titulo} ({self.nota})"

class Grupo(models.Model):
    nome = models.CharField(max_length=150)
    jogo_foco = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    estilo = models.CharField(max_length=50, choices=ESTILO_GRUPO_CHOICES, default='Casual')
    descricao = models.TextField(max_length=300, blank=True)
    lider = models.ForeignKey(User, on_delete=models.CASCADE)
    vagas_disponiveis = models.IntegerField()
    membros = models.ManyToManyField(User, related_name='grupos_que_participo', blank=True)


    def __str__(self):
        return self.nome

class SolicitacaoGrupo(models.Model):
    STATUS_CHOICES = (
        ('Pendente', 'Pendente'),
        ('Aprovada', 'Aprovada'),
        ('Rejeitada', 'Rejeitada'),
    )

    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pendente')
    data_solicitacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} -> {self.grupo.nome} ({self.status})"

class MensagemGrupo(models.Model):
    grupo = models.ForeignKey(Grupo, related_name='mensagens', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField(max_length=500)
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} no grupo {self.grupo.nome}"

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='perfis/', blank=True, null=True)
    bio = models.TextField(max_length=300, blank=True)

    def calcular_influencia(self):
        qtd_reviews = self.user.avaliacao_set.count()
        if qtd_reviews < 5:
            return {"rank": "Novato", "cor": "novato"}
        elif qtd_reviews < 10:
            return {"rank": "Explorador", "cor": "explorador"}
        elif qtd_reviews < 20:
            return {"rank": "Crítico Veterano", "cor": "critico_veterano"}
        else: 
            return {"rank": "Lenda do Lobby", "cor": "lenda_lobby"}

    def __str__(self):
        return f"Perfil de {self.user.username}"

class Chato(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField(max_length=280)
    data_publicacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} disse: {self.texto[:20]}..."

class RespostaChato(models.Model):
    chato = models.ForeignKey(Chato, related_name='respostas', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField(max_length=280)
    data_resposta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resposta de {self.usuario.username}"