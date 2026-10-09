from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from .views.ViewPet import (listar_pets, criar_pet, editar_pet, deletar_pet)
from .views.ViewUsuario import (listar_clientes, criar_cliente, editar_cliente, deletar_cliente)
from .views.ViewPoliticas import (politica_privacidade, politica_regulamento, politica_transporte)
from .views.ViewRelatorio import (relatorio)
from .views.ViewAgendamento import (agendamentos, criar_agendamento, editar_agendamento, deletar_agendamento)
from .views.ViewServico import (listar_servicos, salvar_servico, deletar_servico)
from .views.ViewPerfil import (perfil)
from .views.ViewLogin import (login)
from .views.ViewCadastrar import (cadastrar_usuario)


urlpatterns = [

    path('login/', login.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('cadastro/', cadastrar_usuario, name='cadastro'),

    path('politica-privacidade/', politica_privacidade, name='politica-privacidade'),
    path('politica-transporte/', politica_transporte, name='politica-transporte'),
    path('politica-regulamento/', politica_regulamento, name='politica-regulamento'),

    path('perfil/', login_required(perfil), name='perfil'),

    path('pets/', login_required(listar_pets), name='listar_pets'),
    path('pets/novo/', login_required(criar_pet), name='criar_pet'),
    path('pets/<int:pk>/editar/', login_required(editar_pet), name='editar_pet'),
    path('pets/<int:pk>/deletar/', login_required(deletar_pet), name='deletar_pet'),

    path('agendamentos/', login_required(agendamentos), name='agendamentos'),
    path('agendamentos/novo/', login_required(criar_agendamento), name='criar_agendamento'),
    path('agendamentos/<int:pk>/editar/', login_required(editar_agendamento), name='editar_agendamento'),
    path('agendamentos/<int:pk>/deletar/', login_required(deletar_agendamento), name='deletar_agendamento'),

    path('clientes/', staff_member_required(listar_clientes), name='listar_clientes'),
    path('clientes/novo/', staff_member_required(criar_cliente), name='criar_cliente'),
    path('clientes/<int:pk>/editar/', staff_member_required(editar_cliente), name='editar_cliente'),
    path('clientes/<int:pk>/deletar/', staff_member_required(deletar_cliente), name='deletar_cliente'),

    path('relatorio/', staff_member_required(relatorio), name='relatorio'),

    path('servicos/', staff_member_required(listar_servicos), name='listar_servicos'),
    path('servicos/novo/', staff_member_required(salvar_servico), name='criar_servico'),
    path('servicos/<int:pk>/editar/', staff_member_required(salvar_servico), name='editar_servico'),
    path('servicos/<int:pk>/deletar/', staff_member_required(deletar_servico), name='deletar_servico'),
]