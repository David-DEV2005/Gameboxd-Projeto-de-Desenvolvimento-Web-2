import os
from django.shortcuts import render, redirect
from .models import Jogo, Avaliacao, Grupo, SolicitacaoGrupo, Perfil, Chato, RespostaChato, MensagemGrupo, User
# from django.contrib.auth.forms import UserCreationForm
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


def index(request):
    total_jogos = Jogo.objects.count()
    total_reviews = Avaliacao.objects.count()
    total_usuarios = User.objects.count()


    # Puxa as 3 avaliações mais recentes pela data de publicação
    ultimas_reviews = Avaliacao.objects.select_related('usuario', 'jogo').order_by('-data_publicacao')[:3]


    #Como as notas já estão salvas no banco, podemos ordernar diretamente por ela. 
    jogos_em_alta = Jogo.objects.order_by('-nota_media')[:3]

    ultimos_chatos = Chato.objects.select_related('usuario').order_by('-data_publicacao')[:3]

    jogos = Jogo.objects.all()

    url = f'https://gnews.io/api/v4/search?q=videogame OR esports&lang=pt&country=br&max=5&apikey={os.environ.get('API_KEY')}'
   
    try:
        resposta = requests.get(url, timeout=3)
        dados = resposta.json()
        artigos = dados.get('articles', [])
    except requests.exceptions.RequestException:
        artigos = []


    context = {
        'total_jogos': total_jogos,
        'total_reviews': total_reviews,
        'total_usuarios': total_usuarios,
        'ultimas_reviews': ultimas_reviews,
        'jogos': jogos,
        'jogos_em_alta': jogos_em_alta,
        'noticias': artigos,
        'ultimos_chatos': ultimos_chatos,
    }


    return render(request, 'lobby/index.html', context)



def add_game(request):
     # Se o usuário clicou no botão "salvar" do formulário
    if request.method == 'POST':
        titulo_digitado = request.POST.get('titulo')
        genero_digitado = request.POST.get('genero')
        plataforma_digitada = request.POST.get('plataforma')

        # Verifica se já existe um jogo com esse exato título no banco
        jogo_existente = Jogo.objects.filter(
            titulo__iexact=titulo_digitado).first()

        if jogo_existente:
            # Se o jogo já existe, redireciona o usuário para a página desse jogo específico
            return redirect('game_wall', id=jogo_existente.id)
        else:
            # Se não existe, cria o jogo novo no banco de dados
            novo_jogo = Jogo.objects.create(
                titulo=titulo_digitado,
                genero=genero_digitado,
                plataforma=plataforma_digitada
            )
            # Redireciona para a página do jogo que acabou de ser criado
            return redirect('game_wall', id=novo_jogo.id)

    # Se o usuário só acessou a página pelo link, mostra o formulário HTML vazio
    return render(request, 'lobby/add_game.html')


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
        novo_grupo = Grupo.objects.create(
            jogo_foco=jogo,
            lider=request.user,
            nome=nome_digitado,
            vagas_disponiveis=int(vagas_digitadas)
        )
        novo_grupo.membros.add(request.user)

        return redirect('game_wall', id=jogo.id)

    return render(request, 'lobby/group.html', {'jogo': jogo})


@login_required
def solicitar_entrada(request, grupo_id):
    grupo = Grupo.objects.get(id=grupo_id)

    if request.user == grupo.lider:
        return redirect('game_wall', id=grupo.jogo_foco.id)

    ja_solicitou = SolicitacaoGrupo.objects.filter(
        grupo=grupo, usuario=request.user).exists()

    if not ja_solicitou:
        SolicitacaoGrupo.objects.create(
            grupo=grupo,
            usuario=request.user
        )

    return redirect('game_wall', id=grupo.jogo_foco.id)

@login_required
def sair_do_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)
    
    # Se o usuário atual for o líder, precisamos passar o cargo adiante
    if grupo.lider == request.user:
        # Busca o primeiro membro cadastrado que não seja o próprio líder
        proximo_lider = grupo.membros.exclude(id=request.user.id).first()
        
        if proximo_lider:
            grupo.lider = proximo_lider
            grupo.save()
            
    # Remove o usuário da lista de membros ativos
    grupo.membros.remove(request.user)
    
    # Se não restou mais ninguém no grupo, ele é deletado
    if grupo.membros.count() == 0:
        grupo.delete()
        
    return redirect('my_profile')


@login_required
def painel_notificacoes(request):
    meus_grupos = Grupo.objects.filter(lider=request.user)

    solicitacoes_pendentes = SolicitacaoGrupo.objects.filter(
        grupo__in=meus_grupos,
        status='Pendente'
    ).order_by('-data_solicitacao')

    return render(request, 'lobby/notify.html', {
        'solicitacoes': solicitacoes_pendentes,
        'meus_grupos': meus_grupos
    })


@login_required
def responder_solicitacao(request, solicitacao_id, acao):
    if request.method == 'POST':
        solicitacao = SolicitacaoGrupo.objects.get(id=solicitacao_id)

        if request.user == solicitacao.grupo.lider:

            if acao == 'aceitar' and solicitacao.grupo.vagas_disponiveis > 0:
                solicitacao.status = 'Aprovada'
                solicitacao.grupo.membros.add(solicitacao.usuario)
                solicitacao.grupo.vagas_disponiveis -= 1
                solicitacao.grupo.save()

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
            # Salva a postagem nova no banco
            Chato.objects.create(usuario=request.user, texto=texto_post)
            
            # Dispara o alarme para acender a bolinha vermelha para todos
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'feed_global_notificacoes', # Nome da sala configurada no consumer
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
            # Salva a resposta da postagem no banco
            RespostaChato.objects.create(
                chato=chato_original,
                usuario=request.user,
                texto=texto_resposta
            )
            
            # Dispara o alarme também quando alguém responde a um post
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'feed_global_notificacoes',
                {
                    'type': 'disparar_alerta'
                }
            )

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


def order_rating(request, id):
    jogo = get_object_or_404(Jogo, id=id)

    ordenacao = request.GET.get('sort', 'recentes')

    filtros_validos = {
        'recentes': '-data_publicacao',
        'antigas': 'data_publicacao',
        'maior_nota': '-nota',
        'menor_nota': 'nota',
    }

    filtro_banco = filtros_validos.get(ordenacao, '-data_publicacao')

    avaliacoes = Avaliacao.objects.filter(jogo=jogo).order_by(filtro_banco)

    context = {
        'jogo': jogo,
        'avaliacoes': avaliacoes,
        'sort_atual': ordenacao,
    }
    return render(request, 'lobby/game_wall.html', context)

def atualizar_chat(request, id):

    grupo = get_object_or_404(Grupo, id=id)
    mensagens = MensagemGrupo.objects.filter(grupo=grupo).order_by('data_envio')
    
    context = {
        'mensagens': mensagens,
        'user': request.user
    }

    return render(request, 'lobby/chat_att.html', context)

@login_required
def aba_noticias(request):
    # Chave real do site
    api_key = settings.MINHA_API_KEY 
    
    # Busca focada no Brasil trazendo até 12 resultados
    termo_de_busca = 'videogame OR playstation OR xbox OR nintendo OR esports'
    url = f'https://gnews.io/api/v4/search?q={termo_de_busca}&lang=pt&country=br&max=12&apikey={api_key}'

    try:
        # Faz a chamada para a internet
        resposta = requests.get(url)
        resposta.raise_for_status() # Verifica se a API não deu erro
        
        dados = resposta.json()
        artigos = dados.get('articles', [])
        
    except requests.exceptions.RequestException as e:
        # Proteção: Se der erro, enviamos uma lista vazia e a tela lida com isso
        artigos = []
        print(f"Erro ao buscar notícias: {e}")

    return render(request, 'lobby/noticies.html', {'noticias': artigos})