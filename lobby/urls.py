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
    
]


