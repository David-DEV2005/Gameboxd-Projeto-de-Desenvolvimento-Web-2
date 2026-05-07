from django.shortcuts import render, redirect
from .models import Jogo, Avaliacao, Grupo, SolicitacaoGrupo
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required


def index(request):
    # Busca todos os jogos cadastrados no banco 
    jogos = Jogo.objects.all()
    # Envia a lista de jogos para o HTML para listar na página inicial
    return render(request, 'lobby/index.html', {'jogos': jogos})

def add_game(request):
    # Se o usuário clicou no botão "salvar" do formulário
    if request.method == 'POST':
        titulo_digitado = request.POST.get('titulo')
        genero_digitado = request.POST.get('genero')
        plataforma_digitada = request.POST.get('plataforma')

        # Verifica se já existe um jogo com esse exato título no banco
        # (O '__iexact' faz a busca ignorar se o usuário digitou com letras maiúsculas ou minúsculas)
        jogo_existente = Jogo.objects.filter(titulo__iexact=titulo_digitado).first()

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
    # Pega o jogo certo no banco
    jogo = Jogo.objects.get(id=id)
    
    #Busca as avaliações apenas desse jogo (o '-data_publicacao' faz ordernar do mais "novo" ao mais "antigo"))
    avaliacoes = Avaliacao.objects.filter(jogo=jogo).order_by('-data_publicacao')
    
    # Busca os grupos que estão recrutando para esse jogo
    grupos = Grupo.objects.filter(jogo_foco=jogo)
    
    # Junta tudo e manda para o HTML 
    contexto = {
        'jogo': jogo,
        'avaliacoes': avaliacoes,
        'grupos': grupos
    }
    
    return render(request, 'lobby/game_wall.html', contexto)

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
        
        # Volta para a página do jogo para ver a review lá
        return redirect('game_wall', id=jogo.id)

    # Se não for POST, mostra a tela vazia com o formulário
    return render(request, 'lobby/rating.html', {'jogo': jogo})

def group(request, id):
    # Puxa o jogo onde o grupo vai ser criado
    jogo = Jogo.objects.get(id=id)

    if request.method == 'POST':
        # Pega os dados digitados no formulário
        nome_digitado = request.POST.get('nome')
        descricao_digitada = request.POST.get('descricao')
        vagas_digitadas = request.POST.get('vagas_disponiveis')

        # Cria o grupo no banco de dados com os dados digitados e o usuario como lider. 
        Grupo.objects.create(
            jogo_foco=jogo,
            lider=request.user,
            nome=nome_digitado,
            descricao=descricao_digitada,
            vagas_disponiveis=int(vagas_digitadas)
        )
        
        # Redireciona de volta para a página do jogo
        return redirect('game_wall', id=jogo.id)

    # Se não for POST, mostra a tela com o formulário vazio
    return render(request, 'lobby/group.html', {'jogo': jogo})

@login_required
def solicitar_entrada(request, grupo_id):
    # Busca o grupo no banco de dados
    grupo = Grupo.objects.get(id=grupo_id)
    
    # O líder não pode pedir para entrar no próprio grupo
    if request.user == grupo.lider:
        return redirect('game_wall', id=grupo.jogo_foco.id)
        
    # Verifica se o usuário já mandou uma solicitação antes para não duplicar
    ja_solicitou = SolicitacaoGrupo.objects.filter(grupo=grupo, usuario=request.user).exists()
    
    if not ja_solicitou:
        # Se não solicitou ainda, cria a solicitação no banco como "Pendente"
        SolicitacaoGrupo.objects.create(
            grupo=grupo,
            usuario=request.user
        )
        
    # Redireciona de volta para a tela do jogo
    return redirect('game_wall', id=grupo.jogo_foco.id)

@login_required
def painel_notificacoes(request):
    # Grupos que eu criei
    meus_grupos = Grupo.objects.filter(lider=request.user)
    
    # Solicitações pendentes 
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
        
        # só o líder do grupo pode aceitar ou recusar
        if request.user == solicitacao.grupo.lider:
            
            if acao == 'aceitar' and solicitacao.grupo.vagas_disponiveis > 0:
                solicitacao.status = 'Aprovada'
                solicitacao.grupo.vagas_disponiveis -= 1
                solicitacao.grupo.save()
                
            elif acao == 'recusar':
                solicitacao.status = 'Rejeitada'
            
            solicitacao.save()
            
    return redirect('painel_notificacoes')


def register(request):
    if request.method == 'POST':
        # Recebe os dados do formulário de criação de usuário
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Salva o novo usuário no banco de dados
            user = form.save()
            # Loga o usuário automaticamente após criar a conta
            login(request, user)
            return redirect('index')
    else:
        # Se não for POST, mostra o formulário vazio
        form = UserCreationForm()

    return render(request, 'lobby/register.html', {'form': form})