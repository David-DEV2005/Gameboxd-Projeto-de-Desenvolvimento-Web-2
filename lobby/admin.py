from django.contrib import admin
from .models import Jogo, Avaliacao, Grupo


class JogoAdmin(admin.ModelAdmin):
    # Mostra a média sem permitir que alguém altere.
    readonly_fields = ('nota_media',)

admin.site.register(Jogo, JogoAdmin)
admin.site.register(Avaliacao)
admin.site.register(Grupo)
