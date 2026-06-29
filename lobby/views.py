from decouple import config
import logging
import os
from django.shortcuts import render, redirect
from .models import Jogo, Avaliacao, Grupo, SolicitacaoGrupo, Perfil, Chato, RespostaChato, MensagemGrupo, User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import PerfilForm
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
import requests
from .forms import RegistroForm 
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.http import JsonResponse

JOGOS_POR_PAGINA = 20
def obter_versao_catalogo():
    return cache.get('catalogo_versao', 1)


def bump_versao_catalogo():
    cache.set('catalogo_versao', obter_versao_catalogo() + 1, None)  # sem TTL, fica até o próximo bump



def index(request):
    estatisticas = cache.get('estatisticas_home')
    if estatisticas is None:
        estatisticas = {
            'total_jogos': Jogo.objects.count(),
            'total_reviews': Avaliacao.objects.count(),
            'total_usuarios': User.objects.count(),
        }
        cache.set('estatisticas_home', estatisticas, 60 * 10)


    # Puxa as 3 avaliações mais recentes pela data de publicação
    ultimas_reviews = Avaliacao.objects.select_related('usuario', 'jogo').order_by('-data_publicacao')[:3]


    # Como você já salva a nota_media no model Jogo, basta ordenar por ela!
    jogos_em_alta = cache.get('jogos_em_alta')
    if jogos_em_alta is None:
        jogos_em_alta = list(Jogo.objects.order_by('-nota_media')[:3])
        cache.set('jogos_em_alta', jogos_em_alta, 60 * 15)


    ultimos_chatos = Chato.objects.select_related('usuario').order_by('-data_publicacao')[:3]


    todos_os_jogos = Jogo.objects.all().order_by('-id')
    paginador = Paginator(todos_os_jogos, JOGOS_POR_PAGINA)
    jogos = paginador.page(1)


    versao = obter_versao_catalogo()
    chave_catalogo = f'catalogo_pagina_1_v{versao}'
    catalogo_html = cache.get(chave_catalogo)
    if catalogo_html is None:
        catalogo_html = render_to_string('lobby/more_games.html', {'jogos': jogos})
        cache.set(chave_catalogo, catalogo_html, 60 * 30)


    artigos = cache.get('noticias_home_index')
    if artigos is None:
        api_key = config('API_KEY')
        url = f'https://gnews.io/api/v4/search?q=videogame OR esports&lang=pt&country=br&max=5&apikey={api_key}'
        try:
            resposta = requests.get(url, timeout=3)
            dados = resposta.json()
            artigos = dados.get('articles', [])
        except requests.exceptions.RequestException:
            artigos = []
        cache.set('noticias_home_index', artigos, 60 * 20)


    context = {
        'total_jogos': estatisticas['total_jogos'],
        'total_reviews': estatisticas['total_reviews'],
        'total_usuarios': estatisticas['total_usuarios'],
        'ultimas_reviews': ultimas_reviews,
        'jogos': jogos,
        'mais_jogos': jogos.has_next(),
        'jogos_em_alta': jogos_em_alta,
        'noticias': artigos,
        'ultimos_chatos': ultimos_chatos,
        'catalogo_html': catalogo_html,
    }


    return render(request, 'lobby/index.html', context)



def add_game(request):
    if request.method == 'POST':
        titulo_digitado = request.POST.get('titulo')
        genero_digitado = request.POST.get('genero')
        plataforma_digitada = request.POST.get('plataforma')
        capa_url_digitada = request.POST.get('capa_url') 

        jogo_existente = Jogo.objects.filter(titulo__iexact=titulo_digitado).first()

        if jogo_existente:
            return redirect('game_wall', id=jogo_existente.id)
        else:
            novo_jogo = Jogo.objects.create(
                titulo=titulo_digitado,
                genero=genero_digitado,
                plataforma=plataforma_digitada,
                capa_url=capa_url_digitada or None 
            )
            bump_versao_catalogo()
            return redirect('game_wall', id=novo_jogo.id)

    return render(request, 'lobby/add_game.html')

def carregar_mais_jogos(request):
    pagina_solicitada = request.GET.get('pagina', 2)
    versao = obter_versao_catalogo()
    chave = f'catalogo_pagina_{pagina_solicitada}_v{versao}'


    resultado_cacheado = cache.get(chave)
    if resultado_cacheado is not None:
        return JsonResponse(resultado_cacheado)


    todos_os_jogos = Jogo.objects.all().order_by('-id')
    paginador = Paginator(todos_os_jogos, JOGOS_POR_PAGINA)


    try:
        pagina_jogos = paginador.page(pagina_solicitada)
    except (EmptyPage, PageNotAnInteger):
        return JsonResponse({'html': '', 'tem_mais': False})


    resultado = {
        'html': render_to_string('lobby/more_games.html', {'jogos': pagina_jogos}, request=request),
        'tem_mais': pagina_jogos.has_next(),
    }


    cache.set(chave, resultado, 60 * 30)
    return JsonResponse(resultado)


def game_wall(request, id):
    jogo = get_object_or_404(Jogo, id=id)
    grupos = Grupo.objects.filter(jogo_foco=jogo)

    ordenacao = request.GET.get('sort', 'recentes')
    
    filtros_validos = {
        'recentes': '-id',
        'antigas': 'id',
        'maior_nota': '-nota',
        'menor_nota': 'nota',
    }

    filtro_banco = filtros_validos.get(ordenacao, '-id')

    avaliacoes = Avaliacao.objects.filter(jogo=jogo).order_by(filtro_banco)

    context = {
        'jogo': jogo,
        'avaliacoes': avaliacoes,
        'sort_atual': ordenacao, 
        'grupos': grupos,
    }

    return render(request, 'lobby/game_wall.html', context)

@login_required
def rating(request, id):
    # Puxa o jogo que vai receber a avaliação
    jogo = Jogo.objects.get(id=id)

    if request.method == 'POST':
        nota_digitada = request.POST.get('nota')
        comentario_digitado = request.POST.get('comentario')
        # Converte a nota para float para salvar no banco de dados
        nota = float(nota_digitada)

        Avaliacao.objects.create(
            jogo=jogo,
            usuario=request.user,
            nota=nota,
            comentario=comentario_digitado
        )

        return redirect('game_wall', id=jogo.id)

    return render(request, 'lobby/rating.html', {'jogo': jogo})


@login_required
def del_rating(request, id):

    avaliacao = get_object_or_404(Avaliacao, id=id)

    if avaliacao.usuario == request.user:
        if request.method == 'POST':
            avaliacao.delete()
            messages.success(request, 'Avaliação apagada com sucesso!')
    else:
        messages.error(
            request, 'Você não tem permissão para apagar esta avaliação.')

    return redirect('my_profile')


def wall_rating(request):
    ordenacao = request.GET.get('sort', 'recentes')

    filtros_validos = {
        'recentes': '-id',
        'antigas': 'id',
        'maior_nota': '-nota',
        'menor_nota': 'nota',
    }

    filtro_banco = filtros_validos.get(ordenacao, '-id')

    avaliacoes = Avaliacao.objects.all().order_by(filtro_banco)

    context = {
        'avaliacoes': avaliacoes,
        'sort_atual': ordenacao,
    }

    return render(request, 'lobby/wall_rating.html', context)


@login_required
def group(request, id):
    jogo = Jogo.objects.get(id=id)

    if request.method == 'POST':
        nome_digitado = request.POST.get('nome')
        vagas_digitadas = request.POST.get('vagas_disponiveis')
        descricao_digitada = request.POST.get('descricao', '')
        estilo_digitado = request.POST.get('estilo', 'Casual')

        novo_grupo = Grupo.objects.create(
            jogo_foco=jogo,
            lider=request.user,
            nome=nome_digitado,
            vagas_disponiveis=int(vagas_digitadas),
            descricao=descricao_digitada,
            estilo=estilo_digitado,
        )
        novo_grupo.membros.add(request.user)

        return redirect('game_wall', id=jogo.id)
   
    return render(request, 'lobby/group.html', {'jogo': jogo})



@login_required
def solicitar_entrada(request, grupo_id):
    grupo = Grupo.objects.get(id=grupo_id)

    if request.user == grupo.lider:
        return redirect('game_wall', id=grupo.jogo_foco.id)

    solicitacao_existente = SolicitacaoGrupo.objects.filter(
        grupo=grupo, usuario=request.user).first()


    if solicitacao_existente is None:
        SolicitacaoGrupo.objects.create(grupo=grupo, usuario=request.user)
    elif solicitacao_existente.status == 'Rejeitada':
        solicitacao_existente.status = 'Pendente'
        solicitacao_existente.save()


    return redirect('game_wall', id=grupo.jogo_foco.id)

@login_required
def sair_do_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)

    if grupo.lider == request.user:

        proximo_lider = grupo.membros.exclude(id=request.user.id).first()
       
        if proximo_lider:
            grupo.lider = proximo_lider
            grupo.save()
           
    grupo.membros.remove(request.user)

    SolicitacaoGrupo.objects.filter(grupo=grupo, usuario=request.user).delete()

    if grupo.membros.count() == 0:
        grupo.delete()

    return redirect('my_profile')


@login_required
def painel_notificacoes(request):
    pendentes = SolicitacaoGrupo.objects.filter(
        grupo__lider=request.user,
        status='Pendente'
    )
    historico = SolicitacaoGrupo.objects.filter(
        grupo__lider=request.user,
        status__in=['Aprovada', 'Rejeitada']
    ).order_by('-data_solicitacao')[:20]

    return render(request, 'lobby/notify.html', {
        'solicitacoes': pendentes,
        'historico': historico
    })


@login_required
def responder_solicitacao(request, solicitacao_id, acao):
    if request.method == 'POST':
        solicitacao = SolicitacaoGrupo.objects.get(id=solicitacao_id)

        if request.user == solicitacao.grupo.lider:
            if acao == 'aceitar':
                if solicitacao.grupo.vagas_disponiveis > 0:
                    solicitacao.status = 'Aprovada'
                    solicitacao.grupo.membros.add(solicitacao.usuario)
                    solicitacao.grupo.vagas_disponiveis -= 1
                    solicitacao.grupo.save()
                    solicitacao.save()
                else:
                    messages.error(request, 'Não há vagas disponíveis neste grupo.')

            elif acao == 'recusar':
                solicitacao.status = 'Rejeitada'
                solicitacao.save()

    return redirect('painel_notificacoes')


def register(request):
   if request.method == 'POST':
       form = RegistroForm(request.POST)
     
       if form.is_valid():
           user = form.save()
           login(request, user) # Faz o login automático
           return redirect('index') # Redireciona para a página principal
   else:        
       form = RegistroForm()
   return render(request, 'lobby/register.html', {'form': form})



@login_required
def my_profile(request):
    perfil, created = Perfil.objects.get_or_create(user=request.user)
    minhas_reviews = Avaliacao.objects.filter(usuario=request.user).order_by('-id')
    meus_grupos = Grupo.objects.filter(Q(lider=request.user) | Q(membros=request.user)).distinct()
    influencia = perfil.calcular_influencia()

    context = {
        'perfil': perfil,
        'reviews': minhas_reviews,
        'meus_grupos': meus_grupos,
        'influencia': influencia
    }

    return render(request, 'lobby/profile.html', context)

@login_required
def editar_perfil(request):
    perfil, created = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('my_profile')
    else:
        form = PerfilForm(instance=perfil)

    return render(request, 'lobby/edit_profile.html', {'form': form})


@login_required
def mural_chatos(request):
    if request.method == 'POST':
        texto_post = request.POST.get('texto')
        if texto_post:
            Chato.objects.create(usuario=request.user, texto=texto_post)
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'feed_global_notificacoes', 
                {
                    'type': 'disparar_alerta'
                }
            )
           
            return redirect('mural_chatos')

    posts = Chato.objects.all().order_by('-data_publicacao')
    return render(request, 'lobby/chatos.html', {'posts': posts})

@login_required
def responder_chato(request, post_id):
    if request.method == 'POST':
        texto_resposta = request.POST.get('texto_resposta')
        chato_original = Chato.objects.get(id=post_id)

        if texto_resposta:
            RespostaChato.objects.create(
                chato=chato_original,
                usuario=request.user,
                texto=texto_resposta
            )

            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'feed_global_notificacoes',
                    {
                        'type': 'disparar_alerta'
                    }
                )
            except Exception:
                pass

    return redirect('mural_chatos')


@login_required
def sala_grupo(request, grupo_id):
    grupo = Grupo.objects.get(id=grupo_id)

    is_lider = request.user == grupo.lider
    is_membro = SolicitacaoGrupo.objects.filter(
        grupo=grupo, usuario=request.user, status='Aprovada').exists()

    if not (is_lider or is_membro):
        return redirect('game_wall', id=grupo.jogo_foco.id)

    if request.method == 'POST':
        texto = request.POST.get('texto')
        if texto:
            MensagemGrupo.objects.create(
                grupo=grupo, usuario=request.user, texto=texto)
            return redirect('sala_grupo', grupo_id=grupo.id)

    mensagens = grupo.mensagens.all().order_by('data_envio')

    return render(request, 'lobby/chat_group.html', {
        'grupo': grupo,
        'mensagens': mensagens
    })

@login_required
def atualizar_chat(request, id):
    grupo = get_object_or_404(Grupo, id=id)
    is_lider = request.user == grupo.lider
    is_membro = SolicitacaoGrupo.objects.filter(grupo=grupo, usuario=request.user, status='Aprovada').exists()

    if not (is_lider or is_membro):
        return redirect('game_wall', id=grupo.jogo_foco.id)

    mensagens = MensagemGrupo.objects.filter(grupo=grupo).order_by('data_envio')
    context = {
        'mensagens': mensagens,
        'user': request.user
    }

    return render(request, 'lobby/chat_att.html', context)

@login_required
def aba_noticias(request):
    artigos = cache.get('noticias_home')
    if artigos is None:
        API_KEY = config('API_KEY')
        url = f'https://gnews.io/api/v4/search?q=videogame OR esports&lang=pt&country=br&max=20&apikey={API_KEY}'
        try:
            resposta = requests.get(url, timeout=3)
            dados = resposta.json()
            artigos = dados.get('articles', [])
        except requests.exceptions.RequestException:
            artigos = []
        cache.set('noticias_home', artigos, 60 * 20)


    return render(request, 'lobby/noticies.html', {'noticias': artigos})