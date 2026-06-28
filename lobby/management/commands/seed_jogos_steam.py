import json
import os
from django.core.management.base import BaseCommand
from lobby.models import Jogo
from django.core.cache import cache

PASTA_DO_COMANDO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_JSON = os.path.join(PASTA_DO_COMANDO, 'data', 'games.json')
LIMITE_JOGOS = 300

MAPA_GENERO = {
    'rpg': 'RPG',
    'role-playing': 'RPG',
    'massively multiplayer': 'RPG',
    'strategy': 'Estratégia',
    'sports': 'Esportes',
    'racing': 'Esportes',
    'action': 'Ação',
    'adventure': 'Ação',
    'simulation': 'Ação',
    'casual': 'Arcade',
    'indie': 'Arcade',
    'free to play': 'Arcade',
}


def texto_de_genero_e_tags(generos, tags):
    partes = []

    if isinstance(generos, list):
        partes.extend(generos)
    elif isinstance(generos, str):
        partes.append(generos)

    if isinstance(tags, dict):
        partes.extend(tags.keys())
    elif isinstance(tags, list):
        partes.extend(tags)

    return ' '.join(partes).lower()


def mapear_genero(generos, tags):
    texto = texto_de_genero_e_tags(generos, tags)

    if 'fps' in texto or 'shooter' in texto:
        return 'FPS'
    if 'fighting' in texto or 'arcade' in texto:
        return 'Arcade'

    for chave, valor in MAPA_GENERO.items():
        if chave in texto:
            return valor

    return 'Ação'


def limpar_capa_url(valor_bruto):
    valor = (valor_bruto or '').strip()

    if not valor.startswith('http'):
        return None
    if len(valor) > 500:
        return None

    return valor


class Command(BaseCommand):
    help = 'Importa um catálogo inicial de jogos a partir do dataset da Steam (Kaggle), via JSON.'

    def handle(self, *args, **options):
        criados = 0
        ignorados = 0

        self.stdout.write('Carregando o JSON, isso pode levar alguns segundos...')

        with open(CAMINHO_JSON, encoding='utf-8') as arquivo:
            dados = json.load(arquivo)

        jogos_brutos = list(dados.values())
        jogos_brutos.sort(key=lambda j: int(j.get('recommendations') or 0), reverse=True)

        for jogo_bruto in jogos_brutos[:LIMITE_JOGOS]:
            titulo = (jogo_bruto.get('name') or '').strip()[:200]

            if not titulo or Jogo.objects.filter(titulo__iexact=titulo).exists():
                ignorados += 1
                continue

            try:
                Jogo.objects.create(
                    titulo=titulo,
                    genero=mapear_genero(jogo_bruto.get('genres'), jogo_bruto.get('tags')),
                    plataforma='PC',
                    capa_url=limpar_capa_url(jogo_bruto.get('header_image')),
                )
                criados += 1
            except Exception as erro:
                self.stdout.write(self.style.WARNING(f'Pulei "{titulo}": {erro}'))
                ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f'{criados} jogos importados. {ignorados} ignorados (duplicados ou sem título).'
        ))
        
cache.set('catalogo_versao', cache.get('catalogo_versao', 1) + 1, None)