from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .decorators import administrador_required

from .views.ViewPet import (listar_pets, criar_pet, editar_pet, deletar_pet)
from .views.ViewUsuario import (
    listar_clientes,
    criar_cliente,
    editar_cliente,
    alterar_senha_cliente,
    deletar_cliente,
)
from .views.ViewColaborador import (
    listar_colaboradores,
    criar_colaborador,
    editar_colaborador,
    alternar_status_colaborador,
)
from .views.ViewHorario import (
    gerenciar_disponibilidade,
    editar_excecao_horario,
    deletar_excecao_horario,
)
from .views.ViewPoliticas import (politica_privacidade, politica_regulamento, politica_transporte)
from .views.ViewRelatorio import (relatorio)
from .views.ViewAgendamento import (
    agendamentos,
    horarios_disponiveis_json,
    alterar_status_agendamento,
    criar_agendamento,
    editar_agendamento,
    deletar_agendamento,
)
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
    path('agendamentos/horarios-disponiveis/', horarios_disponiveis_json, name='horarios_disponiveis'),
    path(
        'agendamentos/<int:pk>/status/',
        alterar_status_agendamento,
        name='alterar_status_agendamento',
    ),
    path('agendamentos/novo/', login_required(criar_agendamento), name='criar_agendamento'),
    path('agendamentos/<int:pk>/editar/', login_required(editar_agendamento), name='editar_agendamento'),
    path('agendamentos/<int:pk>/deletar/', login_required(deletar_agendamento), name='deletar_agendamento'),

    path('clientes/', administrador_required(listar_clientes), name='listar_clientes'),
    path('clientes/novo/', administrador_required(criar_cliente), name='criar_cliente'),
    path('clientes/<int:pk>/editar/', administrador_required(editar_cliente), name='editar_cliente'),
    path('clientes/<int:pk>/senha/', administrador_required(alterar_senha_cliente), name='alterar_senha_cliente'),
    path('clientes/<int:pk>/deletar/', administrador_required(deletar_cliente), name='deletar_cliente'),

    path('colaboradores/', administrador_required(listar_colaboradores), name='listar_colaboradores'),
    path('colaboradores/novo/', administrador_required(criar_colaborador), name='criar_colaborador'),
    path('colaboradores/<int:pk>/editar/', administrador_required(editar_colaborador), name='editar_colaborador'),
    path('colaboradores/<int:pk>/status/', administrador_required(alternar_status_colaborador), name='alternar_status_colaborador'),

    path('disponibilidade/', administrador_required(gerenciar_disponibilidade), name='gerenciar_disponibilidade'),
    path('disponibilidade/excecao/<int:pk>/editar/', administrador_required(editar_excecao_horario), name='editar_excecao_horario'),
    path('disponibilidade/excecao/<int:pk>/deletar/', administrador_required(deletar_excecao_horario), name='deletar_excecao_horario'),

    path('relatorio/', login_required(relatorio), name='relatorio'),

    path('servicos/', listar_servicos, name='listar_servicos'),
    path('servicos/novo/', salvar_servico, name='criar_servico'),
    path('servicos/<int:pk>/editar/', salvar_servico, name='editar_servico'),
    path('servicos/<int:pk>/deletar/', deletar_servico, name='deletar_servico'),
]