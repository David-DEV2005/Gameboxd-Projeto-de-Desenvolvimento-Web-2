from django.db import models
from django.contrib.auth.models import User 

class Jogo(models.Model):
    titulo = models.CharField(max_length=200)
    genero = models.CharField(max_length=100)
    plataforma = models.CharField(max_length=100)
    nota_media = models.FloatField(default=0.0)

    def __str__(self):
        return self.titulo

class Avaliacao(models.Model):
    jogo = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.FloatField()
    comentario = models.TextField()
    data_publicacao = models.DateTimeField(auto_now_add=True)

class Grupo(models.Model):
    nome = models.CharField(max_length=150)
    jogo_foco = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    lider = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.TextField()
    vagas_disponiveis = models.IntegerField()

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
    
class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='perfis/', default='perfis/default.png', blank=True)
    bio = models.TextField(max_length=300, blank=True)

    def calcular_influencia(self):
        qtd_reviews = self.user.avaliacao_set.count()
        if qtd_reviews < 3:
            return {"rank": "Novato", "cor": "secondary"}
        elif qtd_reviews < 10:
            return {"rank": "Explorador", "cor": "info"}
        elif qtd_reviews < 20:
            return {"rank": "Crítico Veterano", "cor": "warning"}
        else:
            return {"rank": "Lenda do Lobby", "cor": "danger"}

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