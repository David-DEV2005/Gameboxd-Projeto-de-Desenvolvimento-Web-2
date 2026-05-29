from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),

    path('jogo/adicionar/', views.add_game, name='add_game'),

    path('jogo/<int:id>/', views.game_wall, name='game_wall'),

    path('jogo/<int:id>/avaliar/', views.rating, name='rating'),

    path('jogo/<int:id>/grupo/novo/', views.group, name='group'),

    path('register/', views.register, name='register'),
    
    path('login/', auth_views.LoginView.as_view(template_name='lobby/login.html'), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('grupo/<int:grupo_id>/solicitar/', views.solicitar_entrada, name='solicitar_entrada'),

    path('notificacoes/', views.painel_notificacoes, name='painel_notificacoes'),
    
    path('notificacoes/<int:solicitacao_id>/<str:acao>/', views.responder_solicitacao, name='responder_solicitacao'),

    path('avaliacoes/', views.wall_rating, name='wall_rating'),

    path('perfil/', views.my_profile, name='my_profile'),

    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    path('chatos/', views.mural_chatos, name='mural_chatos'),
    
    path('chatos/<int:post_id>/responder/', views.responder_chato, name='responder_chato'),

    path('grupo/<int:grupo_id>/sala/', views.sala_grupo, name='sala_grupo'),

    path('alterar-senha/', auth_views.PasswordChangeView.as_view(template_name='lobby/password_change.html', success_url='/perfil/'), name='password_change'),

    path('avaliacao/<int:id>/deletar/', views.del_rating, name='deletar_avaliacao'),
    
    path('grupo/<int:id>/atualizar-chat/', views.atualizar_chat, name='atualizar_chat'),

    path('grupo/<int:grupo_id>/sair/', views.sair_do_grupo, name='sair_do_grupo'),
    
    path('noticias/', views.aba_noticias, name='noticias'),

    path('recuperar-senha/', auth_views.PasswordResetView.as_view(template_name='lobby/password_rec.html'), name='password_reset'),

    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='lobby/password_rec_env.html'), name='password_reset_done'),

    path('recuperar-senha/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='lobby/password_new.html'), name='password_reset_confirm'),

    path('recuperar-senha/concluido/', auth_views.PasswordResetCompleteView.as_view(template_name='lobby/password_conc.html'), name='password_reset_complete'),






]


