from django.db import models
from django.contrib.auth.models import User # O Django já traz uma tabela de Usuário pronta!

class Jogo(models.Model):
    titulo = models.CharField(max_length=200)
    genero = models.CharField(max_length=100)
    plataforma = models.CharField(max_length=100)
    nota_media = models.FloatField(default=0.0)

    def str(self):
        return self.titulo

class Avaliacao(models.Model):
    jogo = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.IntegerField() # Ex: 1 a 5
    comentario = models.TextField()
    data_publicacao = models.DateTimeField(auto_now_add=True)

class Grupo(models.Model):
    nome = models.CharField(max_length=150)
    jogo_foco = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    lider = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.TextField()
    vagas_disponiveis = models.IntegerField()

    def str(self):
        return self.nome

