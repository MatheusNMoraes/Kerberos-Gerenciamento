from django.urls import path
from django.contrib.auth import views as auth_views
from .views.ViewPet import (listar_pets, criar_pet, editar_pet, deletar_pet)
from .views.ViewUsuario import (listar_clientes, criar_cliente, editar_cliente, deletar_cliente)
from .views.ViewPoliticas import (politica_privacidade, politica_regulamento, politica_transporte)
from .views.ViewRelatorio import (relatorio)
from .views.ViewAgendamento import (agendamentos, criar_agendamento, editar_agendamento, deletar_agendamento)
from .views.ViewPerfil import (perfil)
from .views.ViewLogin import (login)
from .views.ViewCadastrar import (cadastrar_usuario)


urlpatterns = [
    path('clientes/', listar_clientes, name='listar_clientes'),
    path('clientes/novo/', criar_cliente, name='criar_cliente'),
    path('clientes/<int:pk>/editar/', editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/deletar/', deletar_cliente, name='deletar_cliente'),

    path('perfil/', perfil , name='perfil'),

    path('pets/', listar_pets, name='listar_pets'),
    path('pets/novo/', criar_pet, name='criar_pet'),
    path('pets/<int:pk>/editar/', editar_pet, name='editar_pet'),
    path('pets/<int:pk>/deletar/', deletar_pet, name='deletar_pet'),

    path('relatorio/', relatorio , name='relatorio'),

    path('agendamentos/', agendamentos, name='agendamentos'),
    path('agendamentos/novo/', criar_agendamento, name='criar_agendamento'),
    path('agendamentos/<int:pk>/editar/', editar_agendamento, name='editar_agendamento'),
    path('agendamentos/<int:pk>/deletar/', deletar_agendamento, name='deletar_agendamento'),

    path('politica-privacidade/', politica_privacidade , name='politica-privacidade'),
    path('politica-transporte/', politica_transporte , name='politica-transporte'),
    path('politica-regulamento/', politica_regulamento , name='politica-regulamento'),

    path('login/', login.as_view(template_name='login/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('cadastro/', cadastrar_usuario, name='cadastro'),
]