from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),

    path('jogo/adicionar/', views.add_game, name='add_game'),

    path('jogo/<int:id>/', views.game_wall, name='game_wall'),

    path('jogo/<int:id>/avaliar/', views.rating, name='rating'),

    path('jogo/<int:id>/grupo/novo/', views.group, name='group'),
]
