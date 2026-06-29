from .models import SolicitacaoGrupo

def notificacoes(request):
    if request.user.is_authenticated:
        total = SolicitacaoGrupo.objects.filter(
            grupo__lider=request.user,
            status='Pendente'
        ).count()
        return {'total_notificacoes': total}
    return {'total_notificacoes': 0}