from datetime import date, datetime, time, timedelta
from decimal import Decimal
import re

from django.test import Client, TestCase
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from kerberos.forms.FormAgendamento import AgendamentoForm
from kerberos.forms.FormAdminUsuario import AdminUsuarioCreationForm
from kerberos.forms.FormColaborador import ColaboradorForm
from kerberos.forms.FormPet import PetForm
from kerberos.forms.FormUsuario import UsuarioForm
from kerberos.models.agendamento import Agendamento, ItemAgendamento
from kerberos.models.endereco import Endereco
from kerberos.models.pet import Pet
from kerberos.models.servico import Servico
from kerberos.models.transporte import SolicitacaoTransporte
from kerberos.models.usuario import Usuario
from kerberos.models.horario import ExcecaoHorario, HorarioFuncionamento
from kerberos.services.disponibilidade import horarios_disponiveis


class HealthCheckTests(TestCase):
    def test_endpoint_informa_que_aplicacao_responde(self):
        response = self.client.get(reverse('health_check'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')


class PetAuthorizationTests(TestCase):
    def setUp(self):
        self.cliente_a = Usuario.objects.create_user(
            username='cliente_a@email.com',
            email='cliente_a@email.com',
            nome='Cliente A',
            password='Senha@123',
        )
        self.cliente_b = Usuario.objects.create_user(
            username='cliente_b@email.com',
            email='cliente_b@email.com',
            nome='Cliente B',
            password='Senha@123',
        )
        self.pet_a = Pet.objects.create(
            nome='Rex',
            data_de_nascimento=date(2021, 1, 15),
            raca='Vira-lata',
            porte='Pequeno',
            observacao='Pet do cliente A',
            usuario=self.cliente_a,
        )
        self.pet_b = Pet.objects.create(
            nome='Luna',
            data_de_nascimento=date(2020, 5, 20),
            raca='Poodle',
            porte='Médio',
            observacao='Pet do cliente B',
            usuario=self.cliente_b,
        )

    def test_cliente_somente_ve_seus_pets(self):
        self.client.force_login(self.cliente_a)
        response = self.client.get(reverse('listar_pets'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pet_a.nome)
        self.assertNotContains(response, self.pet_b.nome)
        self.assertContains(response, self.cliente_a.nome)
        self.assertNotContains(response, self.cliente_a.email)

    def test_form_pet_associa_usuario_logado(self):
        data = {
            'nome': 'Bidu',
            'data_de_nascimento': '2022-07-10',
            'raca': 'Shih Tzu',
            'porte': 'Pequeno',
            'observacao': 'Pet do cliente A',
        }
        form = PetForm(data=data, user=self.cliente_a)

        self.assertTrue(form.is_valid(), form.errors)
        pet = form.save()
        self.assertEqual(pet.usuario, self.cliente_a)

    def test_form_pet_rejeita_data_de_nascimento_anterior_a_100_anos(self):
        data = {
            'nome': 'Bidu',
            'data_de_nascimento': '0001-01-01',
            'raca': 'Shih Tzu',
            'porte': 'Pequeno',
            'observacao': '',
        }
        form = PetForm(data=data, user=self.cliente_a)

        self.assertFalse(form.is_valid())
        self.assertIn('data_de_nascimento', form.errors)

    def test_confirmacao_de_exclusao_nao_interpola_nome_em_javascript(self):
        self.pet_a.nome = "Rex'); alert(1);//"
        self.pet_a.save()
        self.client.force_login(self.cliente_a)

        response = self.client.get(reverse('listar_pets'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'onsubmit=')
        self.assertContains(
            response,
            'data-confirm-message="Tem certeza que deseja remover este pet?"',
        )


class UsuarioFormPasswordTests(TestCase):
    def setUp(self):
        self.data = {
            'nome': 'Cliente de Teste',
            'email': 'cliente@example.com',
            'telefone': '(11) 91234-5678',
            'senha': 'L0ng-Unique-Password!2026',
            'confirmar_senha': 'L0ng-Unique-Password!2026',
        }

    def test_cadastro_rejeita_senha_fraca(self):
        self.data['senha'] = '12345678'
        self.data['confirmar_senha'] = '12345678'
        form = UsuarioForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn('senha', form.errors)

    def test_cadastro_armazenha_senha_com_hash(self):
        form = UsuarioForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)
        usuario = form.save()

        self.assertTrue(usuario.check_password(self.data['senha']))
        self.assertNotEqual(usuario.password, self.data['senha'])

    def test_edicao_sem_senha_preserva_credencial(self):
        usuario = Usuario.objects.create_user(
            username='cliente@example.com',
            email='cliente@example.com',
            nome='Cliente de Teste',
            password='Existing-Strong-Password!2026',
        )
        data = {
            'nome': 'Cliente Atualizado',
            'email': 'cliente@example.com',
            'telefone': '(11) 91234-5678',
            'senha': '',
            'confirmar_senha': '',
        }
        form = UsuarioForm(data=data, instance=usuario)

        self.assertTrue(form.is_valid(), form.errors)
        usuario_atualizado = form.save()

        self.assertTrue(
            usuario_atualizado.check_password('Existing-Strong-Password!2026')
        )

    def test_edicao_de_perfil_preserva_permissao_staff(self):
        usuario = Usuario.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            nome='Administrador',
            password='Existing-Strong-Password!2026',
            is_staff=True,
        )
        data = {
            'nome': 'Administrador Atualizado',
            'email': 'admin@example.com',
            'telefone': '(11) 91234-5678',
            'senha': '',
            'confirmar_senha': '',
        }
        form = UsuarioForm(data=data, instance=usuario)

        self.assertTrue(form.is_valid(), form.errors)
        usuario_atualizado = form.save()

        self.assertTrue(usuario_atualizado.is_staff)

    def test_telefone_opcional_aceita_vazio(self):
        data = self.data.copy()
        data['telefone'] = ''
        form = UsuarioForm(data=data)

        self.assertTrue(form.is_valid(), form.errors)


class CadastroUsuarioPetTests(TestCase):
    def test_cadastro_separa_nome_do_tutor_e_do_pet(self):
        response = self.client.post(
            reverse('cadastro'),
            {
                'usuario-nome': 'Ana Tutora',
                'usuario-email': 'ana@example.com',
                'usuario-telefone': '(11) 91234-5678',
                'usuario-senha': 'Strong-Password!2026',
                'usuario-confirmar_senha': 'Strong-Password!2026',
                'usuario-aceita_regulamento': 'on',
                'endereco-cep': '01001-000',
                'endereco-logradouro': 'Praça da Sé',
                'endereco-numero': '1',
                'endereco-complemento': '',
                'endereco-bairro': 'Sé',
                'endereco-cidade': 'São Paulo',
                'endereco-uf': 'SP',
                'pet-nome': 'Rex',
                'pet-data_de_nascimento': '2021-01-15',
                'pet-raca': 'Vira-lata',
                'pet-porte': 'Pequeno',
                'pet-observacao': '',
            },
        )

        self.assertRedirects(response, reverse('login'))
        usuario = Usuario.objects.get(email='ana@example.com')
        pet = Pet.objects.get(nome='Rex')
        self.assertEqual(usuario.nome, 'Ana Tutora')
        self.assertEqual(usuario.endereco.logradouro, 'Praça da Sé')
        self.assertEqual(pet.usuario, usuario)


class UsuarioLoginTests(TestCase):
    def test_tela_login_solicita_email(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, 'type="email"')
        self.assertContains(response, 'E-mail')

    @override_settings(CSRF_TRUSTED_ORIGINS=['https://localhost:8001'])
    def test_login_aceita_post_com_origem_https_confiavel(self):
        usuario = Usuario.objects.create_user(
            username='csrf-login',
            email='csrf-login@example.com',
            nome='Login CSRF',
            password='Strong-CSRF-Password!2026',
        )
        cliente_csrf = Client(enforce_csrf_checks=True)
        pagina_login = cliente_csrf.get(
            reverse('login'),
            HTTP_HOST='localhost:8001',
        )
        token = re.search(
            rb'name="csrfmiddlewaretoken" value="([^\"]+)"',
            pagina_login.content,
        ).group(1).decode()

        resposta = cliente_csrf.post(
            reverse('login'),
            {
                'username': usuario.email,
                'password': 'Strong-CSRF-Password!2026',
                'csrfmiddlewaretoken': token,
            },
            HTTP_HOST='localhost:8001',
            HTTP_ORIGIN='https://localhost:8001',
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(int(cliente_csrf.session['_auth_user_id']), usuario.pk)

    def test_usuario_pode_entrar_com_email_quando_username_e_diferente(self):
        usuario = Usuario.objects.create_user(
            username='nome-interno',
            email='cliente-login@example.com',
            nome='Cliente Login',
            password='Strong-Login-Password!2026',
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': usuario.email,
                'password': 'Strong-Login-Password!2026',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            usuario.pk,
        )

    def test_login_de_cliente_rejeita_username_que_nao_seja_email(self):
        usuario = Usuario.objects.create_user(
            username='cliente-login',
            email='cliente-login@example.com',
            nome='Cliente Login',
            password='Strong-Login-Password!2026',
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': usuario.username,
                'password': 'Strong-Login-Password!2026',
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_administrador_pode_entrar_pelo_login_do_site(self):
        usuario = Usuario.objects.create_user(
            username='admin-login',
            email='admin-login@example.com',
            nome='Administrador',
            password='Strong-Login-Password!2026',
            is_staff=True,
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': usuario.email,
                'password': 'Strong-Login-Password!2026',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('listar_clientes'))
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

    def test_login_do_site_nao_aceita_username_no_lugar_de_email(self):
        usuario = Usuario.objects.create_user(
            username='admin-login',
            email='admin-login@example.com',
            nome='Administrador',
            password='Strong-Login-Password!2026',
            is_staff=True,
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': usuario.username,
                'password': 'Strong-Login-Password!2026',
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_admin_cria_usuario_com_senha_hasheada(self):
        senha = 'Strong-Admin-Password!2026'
        form = AdminUsuarioCreationForm(data={
            'username': 'usuario-criado-admin',
            'email': 'admin-created@example.com',
            'nome': 'Usuário Criado',
            'telefone': '',
            'password1': senha,
            'password2': senha,
            'is_active': True,
            'is_staff': False,
        })

        self.assertTrue(form.is_valid(), form.errors)
        usuario = form.save()

        self.assertTrue(usuario.check_password(senha))
        self.assertNotEqual(usuario.password, senha)


class AdminClienteSenhaTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin-senha',
            email='admin-senha@example.com',
            nome='Admin Senha',
            password='Original-Admin-Password!2026',
            is_staff=True,
        )
        self.cliente = Usuario.objects.create_user(
            username='cliente-senha',
            email='cliente-senha@example.com',
            nome='Cliente Senha',
            password='Original-Client-Password!2026',
        )

    def test_staff_pode_definir_nova_senha_com_hash(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('listar_clientes'))
        self.assertContains(
            response,
            reverse('alterar_senha_cliente', args=[self.cliente.pk]),
        )

        response = self.client.get(
            reverse('alterar_senha_cliente', args=[self.cliente.pk]),
        )
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')

        response = self.client.post(
            reverse('alterar_senha_cliente', args=[self.cliente.pk]),
            {
                'password1': 'New-Client-Password!2026',
                'password2': 'New-Client-Password!2026',
            },
        )

        self.assertRedirects(response, reverse('listar_clientes'))
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.check_password('New-Client-Password!2026'))
        self.assertFalse(self.cliente.check_password('Original-Client-Password!2026'))
        self.assertNotEqual(self.cliente.password, 'New-Client-Password!2026')

    def test_cliente_nao_pode_redefinir_senha_de_outro_usuario(self):
        self.client.force_login(self.cliente)

        response = self.client.get(
            reverse('alterar_senha_cliente', args=[self.admin.pk]),
        )

        self.assertEqual(response.status_code, 302)

    def test_staff_nao_define_senha_fraca(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('alterar_senha_cliente', args=[self.cliente.pk]),
            {'password1': '12345678', 'password2': '12345678'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.check_password('Original-Client-Password!2026'))


class ColaboradorTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin-colaboradores',
            email='admin-colaboradores@example.com',
            nome='Admin Colaboradores',
            password='Strong-Admin-Password!2026',
            is_staff=True,
        )
        self.cliente = Usuario.objects.create_user(
            username='cliente-colaboradores@example.com',
            email='cliente-colaboradores@example.com',
            nome='Cliente Colaboradores',
            password='Strong-Client-Password!2026',
        )
        self.pet = Pet.objects.create(
            nome='Toby',
            data_de_nascimento=date(2021, 4, 10),
            raca='SRD',
            porte='Pequeno',
            usuario=self.cliente,
        )

    def criar_colaborador(self, email='colaborador@example.com'):
        form = ColaboradorForm(data={
            'nome': 'Colaborador Teste',
            'email': email,
            'telefone': '',
            'is_active': True,
            'senha': 'Strong-Collaborator-Password!2026',
            'confirmar_senha': 'Strong-Collaborator-Password!2026',
        })
        self.assertTrue(form.is_valid(), form.errors)
        return form.save()

    def test_form_cria_colaborador_sem_permissao_de_administrador(self):
        colaborador = self.criar_colaborador()

        self.assertTrue(colaborador.is_staff)
        self.assertTrue(colaborador.is_colaborador)
        self.assertFalse(colaborador.is_superuser)
        self.assertTrue(
            colaborador.check_password('Strong-Collaborator-Password!2026')
        )

    def test_admin_pode_cadastrar_editar_e_desativar_colaborador(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('criar_colaborador'),
            {
                'nome': 'Novo Colaborador',
                'email': 'novo-colaborador@example.com',
                'telefone': '',
                'is_active': 'on',
                'senha': 'Strong-New-Collaborator-Password!2026',
                'confirmar_senha': 'Strong-New-Collaborator-Password!2026',
            },
        )
        self.assertRedirects(response, reverse('listar_colaboradores'))
        colaborador = Usuario.objects.get(email='novo-colaborador@example.com')
        self.assertTrue(colaborador.is_colaborador)

        response = self.client.post(
            reverse('editar_colaborador', args=[colaborador.pk]),
            {
                'nome': 'Colaborador Atualizado',
                'email': 'novo-colaborador@example.com',
                'telefone': '',
                'is_active': 'on',
                'senha': '',
                'confirmar_senha': '',
            },
        )
        self.assertRedirects(response, reverse('listar_colaboradores'))
        colaborador.refresh_from_db()
        self.assertEqual(colaborador.nome, 'Colaborador Atualizado')
        self.assertTrue(
            colaborador.check_password('Strong-New-Collaborator-Password!2026')
        )

        response = self.client.post(
            reverse('alternar_status_colaborador', args=[colaborador.pk]),
        )
        self.assertRedirects(response, reverse('listar_colaboradores'))
        colaborador.refresh_from_db()
        self.assertFalse(colaborador.is_active)

    def test_colaborador_acessa_agenda_e_consulta_pets_sem_acesso_administrativo(self):
        colaborador = self.criar_colaborador()
        self.client.force_login(colaborador)

        agenda_response = self.client.get(reverse('agendamentos'))
        pets_response = self.client.get(reverse('listar_pets'))
        self.assertEqual(agenda_response.status_code, 200)
        self.assertEqual(pets_response.status_code, 200)
        self.assertContains(pets_response, self.pet.nome)
        self.assertNotContains(pets_response, reverse('editar_pet', args=[self.pet.pk]))
        self.assertNotContains(agenda_response, reverse('listar_colaboradores'))

        for url_name in ('listar_clientes', 'listar_colaboradores', 'listar_servicos'):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)

        self.client.raise_request_exception = False
        self.assertEqual(
            self.client.get(reverse('relatorio')).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse('deletar_pet', args=[self.pet.pk])).status_code,
            403,
        )

    def test_cliente_nao_acessa_a_gestao_de_colaboradores(self):
        self.client.force_login(self.cliente)

        response = self.client.get(reverse('listar_colaboradores'))

        self.assertEqual(response.status_code, 302)

    def test_admin_configura_expediente_semanal_e_dia_fechado(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('gerenciar_disponibilidade'))
        self.assertContains(response, 'Horário semanal')

        dados_semanais = {'acao': 'salvar_semana'}
        dados_semanais.update({
            'dia-0-hora_abertura': '09:00',
            'dia-0-hora_fechamento': '18:00',
        })
        for dia in range(1, 7):
            dados_semanais[f'dia-{dia}-fechado'] = 'on'

        response = self.client.post(reverse('gerenciar_disponibilidade'), dados_semanais)

        self.assertRedirects(response, reverse('gerenciar_disponibilidade'))
        horario = HorarioFuncionamento.objects.get(dia_semana=0)
        self.assertFalse(horario.fechado)
        self.assertEqual(horario.hora_abertura, time(9))
        self.assertEqual(horario.hora_fechamento, time(18))

        data_fechada = (timezone.localdate() + timedelta(days=10)).isoformat()
        response = self.client.post(
            reverse('gerenciar_disponibilidade'),
            {
                'acao': 'criar_excecao',
                'data': data_fechada,
                'fechado': 'on',
                'motivo': 'Feriado',
            },
        )

        self.assertRedirects(response, reverse('gerenciar_disponibilidade'))
        excecao = ExcecaoHorario.objects.get(data=data_fechada)
        self.assertTrue(excecao.fechado)
        self.assertEqual(excecao.motivo, 'Feriado')

    def test_colaborador_nao_pode_alterar_disponibilidade(self):
        colaborador = self.criar_colaborador()
        self.client.force_login(colaborador)

        response = self.client.get(reverse('gerenciar_disponibilidade'))

        self.assertEqual(response.status_code, 302)

    def test_api_retorna_horarios_conforme_dia_e_servicos(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)
        HorarioFuncionamento.objects.create(
            dia_semana=data_selecionada.weekday(),
            fechado=False,
            hora_abertura=time(9),
            hora_fechamento=time(18),
            pausa_inicio=time(12),
            pausa_fim=time(13),
        )
        servico = Servico.objects.create(
            nome='Banho API disponibilidade',
            valor=Decimal('35.00'),
            duracao_minutos=60,
        )
        colaborador = Usuario.objects.create_user(
            username='colaborador-api@example.com',
            email='colaborador-api@example.com',
            nome='Colaborador API',
            password='Strong-Collaborator-Password!2026',
            is_staff=True,
            is_colaborador=True,
        )
        self.client.force_login(self.cliente)

        response = self.client.get(
            reverse('horarios_disponiveis'),
            {
                'data': data_selecionada.isoformat(),
                'servicos': [servico.pk],
                'colaborador': colaborador.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        rotulos = {horario['rotulo'] for horario in response.json()['horarios']}
        self.assertIn('09:00', rotulos)
        self.assertNotIn('12:00', rotulos)
        self.assertNotIn('17:30', rotulos)

        sem_profissional = self.client.get(
            reverse('horarios_disponiveis'),
            {'data': data_selecionada.isoformat(), 'servicos': [servico.pk]},
        )
        self.assertEqual(sem_profissional.json(), {'horarios': []})


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RecuperacaoSenhaTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='cliente-recuperacao',
            email='cliente-recuperacao@example.com',
            nome='Cliente Recuperacao',
            password='Original-Password!2026',
        )

    def test_login_exibe_link_para_recuperar_senha(self):
        response = self.client.get(reverse('login'))

        self.assertContains(response, reverse('password_reset'))

    def test_link_enviado_permite_definir_uma_nova_senha(self):
        response = self.client.post(
            reverse('password_reset'),
            {'email': self.usuario.email},
        )

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.usuario.email, mail.outbox[0].to)

        reset_url = re.search(
            r'http://testserver/accounts/reset/[^\s]+',
            mail.outbox[0].body,
        ).group(0)
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 302)
        set_password_url = response['Location']
        response = self.client.get(set_password_url)
        self.assertContains(response, 'Definir nova senha')
        response = self.client.post(
            set_password_url,
            {
                'new_password1': 'New-Password!2026-Complete',
                'new_password2': 'New-Password!2026-Complete',
            },
        )

        self.assertRedirects(response, reverse('password_reset_complete'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('New-Password!2026-Complete'))

    def test_email_inexistente_nao_revela_se_conta_existe(self):
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'inexistente@example.com'},
        )

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)


class RelatorioAtendimentosTests(TestCase):
    def setUp(self):
        self.staff = Usuario.objects.create_user(
            username='staff@example.com',
            email='staff@example.com',
            nome='Equipe',
            password='Strong-Staff-Password!2026',
            is_staff=True,
        )
        self.cliente = Usuario.objects.create_user(
            username='cliente-relatorio@example.com',
            email='cliente-relatorio@example.com',
            nome='Cliente Relatório',
            password='Strong-Client-Password!2026',
        )
        self.pet = Pet.objects.create(
            nome='Nina',
            data_de_nascimento=date(2022, 2, 1),
            raca='SRD',
            porte='Pequeno',
            usuario=self.cliente,
        )
        self.servico = Servico.objects.create(
            nome='Banho relatório',
            valor=Decimal('30.00'),
            duracao_minutos=30,
        )

    def criar_agendamento(self, status, data):
        agendamento = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            data=data,
            status=status,
        )
        ItemAgendamento.objects.create(
            agendamento=agendamento,
            servico=self.servico,
            servico_nome=self.servico.nome,
            preco_unitario=Decimal('30.00'),
            duracao_minutos=30,
        )
        return agendamento

    def test_relatorio_lista_todos_status_mas_fatura_so_concluidos_passados(self):
        agora = timezone.now()
        self.criar_agendamento(Agendamento.StatusChoices.CONCLUIDO, agora - timedelta(hours=1))
        self.criar_agendamento(Agendamento.StatusChoices.CANCELADO, agora - timedelta(hours=2))
        self.criar_agendamento(Agendamento.StatusChoices.PENDENTE, agora - timedelta(hours=3))
        self.criar_agendamento(Agendamento.StatusChoices.CONCLUIDO, agora + timedelta(hours=1))

        self.client.force_login(self.staff)
        response = self.client.get(
            reverse('relatorio'),
            {
                'data_inicio': (agora.date() - timedelta(days=1)).isoformat(),
                'data_fim': (agora.date() + timedelta(days=1)).isoformat(),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Faturado (concluídos)')
        self.assertContains(response, 'Ticket Médio')
        self.assertEqual(len(response.context['agendamentos']), 4)
        self.assertIn(
            Agendamento.StatusChoices.PENDENTE,
            {agendamento.status for agendamento in response.context['agendamentos']},
        )
        self.assertIn(
            Agendamento.StatusChoices.CANCELADO,
            {agendamento.status for agendamento in response.context['agendamentos']},
        )
        self.assertEqual(response.context['total_atendimentos'], 1)
        self.assertEqual(response.context['total_faturamento'], Decimal('30.00'))

    def test_cliente_acessa_historico_apenas_dos_proprios_agendamentos(self):
        agora = timezone.now()
        agendamento_cliente = self.criar_agendamento(
            Agendamento.StatusChoices.CONCLUIDO,
            agora - timedelta(days=1),
        )

        outro_cliente = Usuario.objects.create_user(
            username='outro-cliente@example.com',
            email='outro-cliente@example.com',
            nome='Outro Cliente',
            password='Strong-Client-Password!2026',
        )
        outro_pet = Pet.objects.create(
            nome='Bolt',
            data_de_nascimento=date(2021, 5, 1),
            raca='SRD',
            porte='Médio',
            usuario=outro_cliente,
        )
        Agendamento.objects.create(
            usuario=outro_cliente,
            pet=outro_pet,
            data=agora - timedelta(days=1),
        )

        self.client.force_login(self.cliente)
        response = self.client.get(
            reverse('relatorio'),
            {
                'data_inicio': (agora.date() - timedelta(days=2)).isoformat(),
                'data_fim': agora.date().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [agendamento.pk for agendamento in response.context['agendamentos']],
            [agendamento_cliente.pk],
        )
        self.assertContains(response, 'Histórico de Agendamentos')
        self.assertNotContains(response, 'Total Investido')
        self.assertNotContains(response, 'Atendimentos Concluídos')
        self.assertNotContains(response, 'Ticket Médio')
        self.assertNotContains(response, 'Bolt')


class AgendamentoHistoricoTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='cliente-agendamento@example.com',
            email='cliente-agendamento@example.com',
            nome='Cliente Agendamento',
            password='Strong-Client-Password!2026',
        )
        self.colaborador = Usuario.objects.create_user(
            username='colaborador-agendamento@example.com',
            email='colaborador-agendamento@example.com',
            nome='Profissional Agendamento',
            password='Strong-Collaborator-Password!2026',
            is_staff=True,
            is_colaborador=True,
        )
        self.pet = Pet.objects.create(
            nome='Toby',
            data_de_nascimento=date(2021, 4, 12),
            raca='SRD',
            porte='Médio',
            usuario=self.cliente,
        )
        self.servico = Servico.objects.create(
            nome='Banho histórico',
            valor=Decimal('30.00'),
            duracao_minutos=30,
        )
        for dia_semana in range(7):
            HorarioFuncionamento.objects.create(
                dia_semana=dia_semana,
                fechado=False,
                hora_abertura=time(9),
                hora_fechamento=time(18),
                pausa_inicio=time(12),
                pausa_fim=time(13),
            )
        data_base = timezone.localdate() + timedelta(days=2)
        self.agendamento = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            colaborador=self.colaborador,
            data=timezone.make_aware(datetime.combine(data_base, time(14))),
        )
        ItemAgendamento.objects.create(
            agendamento=self.agendamento,
            servico=self.servico,
            servico_nome=self.servico.nome,
            preco_unitario=Decimal('25.00'),
            duracao_minutos=25,
        )

    def test_lista_mostra_todos_os_agendamentos_sem_filtro(self):
        outro_agendamento = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            data=self.agendamento.data + timedelta(days=1),
        )
        self.client.force_login(self.cliente)

        response = self.client.get(reverse('agendamentos'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {item.pk for item in response.context['agendamentos']},
            {self.agendamento.pk, outro_agendamento.pk},
        )
        self.assertContains(response, 'Todos os agendamentos')
        self.assertContains(
            response,
            timezone.localtime(outro_agendamento.data).strftime('%d/%m/%Y'),
        )

    def test_lista_filtra_agendamentos_pela_data_escolhida(self):
        outro_agendamento = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            data=self.agendamento.data + timedelta(days=1),
        )
        data_selecionada = timezone.localtime(self.agendamento.data).date()
        self.client.force_login(self.cliente)

        response = self.client.get(
            reverse('agendamentos'),
            {'data': data_selecionada.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item.pk for item in response.context['agendamentos']],
            [self.agendamento.pk],
        )
        self.assertNotIn(
            outro_agendamento.pk,
            [item.pk for item in response.context['agendamentos']],
        )
        self.assertEqual(response.context['data_selecionada'], data_selecionada)

    def test_form_rejeita_agendamento_no_passado(self):
        data_passada = timezone.localtime() - timedelta(days=1)
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_passada.date().isoformat(),
                'data': data_passada.strftime('%Y-%m-%dT%H:%M'),
                'servicos': [self.servico.pk],
            },
            usuario=self.cliente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)

    def test_form_exige_profissional_ativo(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'data_dia': data_selecionada.isoformat(),
                'data': f'{data_selecionada.isoformat()}T09:00',
                'servicos': [self.servico.pk],
            },
            usuario=self.cliente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('colaborador', form.errors)

    def test_criacao_salva_profissional_escolhido(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)
        self.client.force_login(self.cliente)

        response = self.client.post(
            reverse('criar_agendamento'),
            {
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_selecionada.isoformat(),
                'data': f'{data_selecionada.isoformat()}T09:00',
                'servicos': [self.servico.pk],
            },
        )

        self.assertRedirects(response, reverse('agendamentos'))
        agendamento_criado = Agendamento.objects.get(data__date=data_selecionada)
        self.assertEqual(agendamento_criado.colaborador, self.colaborador)

    def test_form_rejeita_data_de_agendamento_do_ano_0001(self):
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': '0001-01-01',
                'data': '0001-01-01T00:00',
                'servicos': [self.servico.pk],
            },
            usuario=self.cliente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)

    def test_edicao_de_agendamento_historico_preserva_data_original(self):
        data_original = timezone.localtime() - timedelta(days=1)
        self.agendamento.data = data_original
        self.agendamento.save(update_fields=['data'])
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_original.date().isoformat(),
                'data': data_original.strftime('%Y-%m-%dT%H:%M'),
                'servicos': [self.servico.pk],
            },
            instance=self.agendamento,
            usuario=self.cliente,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_edicao_historica_valida_duracao_dos_servicos(self):
        data_original = timezone.localtime().replace(
            hour=14, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
        self.agendamento.data = data_original
        self.agendamento.save(update_fields=['data'])
        servico_adicional = Servico.objects.create(
            nome='Tosa histórica longa',
            valor=Decimal('80.00'),
            duracao_minutos=300,
        )
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_original.date().isoformat(),
                'data': data_original.strftime('%Y-%m-%dT%H:%M'),
                'servicos': [self.servico.pk, servico_adicional.pk],
            },
            instance=self.agendamento,
            usuario=self.cliente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)

    def test_lista_mostra_agendamento_fora_de_faixa_de_turno(self):
        data_agendamento = timezone.localtime(self.agendamento.data).replace(
            hour=12, minute=30, second=0, microsecond=0
        )
        self.agendamento.data = data_agendamento
        self.agendamento.save(update_fields=['data'])
        self.client.force_login(self.cliente)

        response = self.client.get(
            reverse('agendamentos'),
            {'data': data_agendamento.date().isoformat()},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '12:30')
        self.assertContains(response, self.pet.nome)
        self.assertContains(response, self.colaborador.nome)
        self.assertContains(response, self.servico.nome)
        self.assertNotContains(response, 'Manhã')

    def test_edicao_preserva_snapshot_de_servico_inativo(self):
        self.servico.valor = Decimal('50.00')
        self.servico.duracao_minutos = 60
        self.servico.ativo = False
        self.servico.save()

        self.client.force_login(self.cliente)
        response = self.client.post(
            reverse('editar_agendamento', args=[self.agendamento.pk]),
            {
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': timezone.localtime(self.agendamento.data).date().isoformat(),
                'data': timezone.localtime(self.agendamento.data).strftime('%Y-%m-%dT%H:%M'),
                'servicos': [self.servico.pk],
            },
            follow=True,
        )

        self.assertContains(response, 'Agendamento atualizado com sucesso!')
        item = ItemAgendamento.objects.get(agendamento=self.agendamento)
        self.assertEqual(item.preco_unitario, Decimal('25.00'))
        self.assertEqual(item.duracao_minutos, 25)

    def test_horarios_disponiveis_respeitam_expediente_pausa_e_duracao(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)

        horarios = horarios_disponiveis(data_selecionada, 60)
        rotulos = {timezone.localtime(horario).strftime('%H:%M') for horario in horarios}

        self.assertIn('09:00', rotulos)
        self.assertIn('11:00', rotulos)
        self.assertNotIn('11:30', rotulos)
        self.assertNotIn('12:00', rotulos)
        self.assertIn('13:00', rotulos)
        self.assertIn('17:00', rotulos)
        self.assertNotIn('17:30', rotulos)

    def test_horarios_disponiveis_excluem_conflitos_por_duracao(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)
        inicio_ocupado = timezone.make_aware(
            datetime.combine(data_selecionada, time(9)),
        )
        agendamento_ocupado = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            data=inicio_ocupado,
        )
        ItemAgendamento.objects.create(
            agendamento=agendamento_ocupado,
            servico=self.servico,
            servico_nome=self.servico.nome,
            preco_unitario=self.servico.valor,
            duracao_minutos=45,
        )

        horarios = horarios_disponiveis(data_selecionada, 30)
        rotulos = {timezone.localtime(horario).strftime('%H:%M') for horario in horarios}

        self.assertNotIn('09:00', rotulos)
        self.assertNotIn('09:30', rotulos)
        self.assertIn('10:00', rotulos)

    def test_horarios_disponiveis_sao_individuais_por_profissional(self):
        outro_colaborador = Usuario.objects.create_user(
            username='outro-colaborador@example.com',
            email='outro-colaborador@example.com',
            nome='Outro Profissional',
            password='Strong-Other-Collaborator-Password!2026',
            is_staff=True,
            is_colaborador=True,
        )
        data_selecionada = timezone.localdate() + timedelta(days=1)
        agendamento_ocupado = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            colaborador=self.colaborador,
            data=timezone.make_aware(datetime.combine(data_selecionada, time(9))),
        )
        ItemAgendamento.objects.create(
            agendamento=agendamento_ocupado,
            servico=self.servico,
            servico_nome=self.servico.nome,
            preco_unitario=self.servico.valor,
            duracao_minutos=45,
        )

        horarios_colaborador = horarios_disponiveis(
            data_selecionada,
            30,
            colaborador_id=self.colaborador.pk,
        )
        horarios_outro = horarios_disponiveis(
            data_selecionada,
            30,
            colaborador_id=outro_colaborador.pk,
        )
        rotulos_colaborador = {
            timezone.localtime(horario).strftime('%H:%M')
            for horario in horarios_colaborador
        }
        rotulos_outro = {
            timezone.localtime(horario).strftime('%H:%M')
            for horario in horarios_outro
        }

        self.assertNotIn('09:00', rotulos_colaborador)
        self.assertIn('09:00', rotulos_outro)

    def test_excecao_de_fechamento_suspende_horarios_semanais(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)
        ExcecaoHorario.objects.create(data=data_selecionada, fechado=True)

        self.assertEqual(horarios_disponiveis(data_selecionada, 30), [])

    def test_excecao_de_horario_especial_substitui_expediente_semanal(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)
        ExcecaoHorario.objects.create(
            data=data_selecionada,
            fechado=False,
            hora_abertura=time(10),
            hora_fechamento=time(12),
        )

        horarios = horarios_disponiveis(data_selecionada, 30)
        rotulos = {timezone.localtime(horario).strftime('%H:%M') for horario in horarios}

        self.assertIn('10:00', rotulos)
        self.assertIn('11:30', rotulos)
        self.assertNotIn('09:00', rotulos)
        self.assertNotIn('12:00', rotulos)

    def test_form_aceita_slot_disponivel_e_rejeita_horario_fora_do_expediente(self):
        data_selecionada = timezone.localdate() + timedelta(days=1)
        form_valido = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_selecionada.isoformat(),
                'data': f'{data_selecionada.isoformat()}T09:00',
                'servicos': [self.servico.pk],
            },
            usuario=self.cliente,
        )
        form_fora_expediente = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_selecionada.isoformat(),
                'data': f'{data_selecionada.isoformat()}T08:30',
                'servicos': [self.servico.pk],
            },
            usuario=self.cliente,
        )

        self.assertTrue(form_valido.is_valid(), form_valido.errors)
        self.assertFalse(form_fora_expediente.is_valid())
        self.assertIn('data', form_fora_expediente.errors)

    def test_edicao_no_mesmo_horario_valida_duracao_dos_servicos_selecionados(self):
        self.servico.duracao_minutos = 300
        self.servico.save(update_fields=['duracao_minutos'])
        data_local = timezone.localtime(self.agendamento.data)
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_local.date().isoformat(),
                'data': data_local.strftime('%Y-%m-%dT%H:%M'),
                'servicos': [self.servico.pk],
            },
            instance=self.agendamento,
            usuario=self.cliente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)

    def test_edicao_no_mesmo_horario_rejeita_conflito_com_outro_agendamento(self):
        self.servico.duracao_minutos = 60
        self.servico.save(update_fields=['duracao_minutos'])
        data_local = timezone.localtime(self.agendamento.data)
        agendamento_conflitante = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            data=data_local + timedelta(minutes=30),
        )
        ItemAgendamento.objects.create(
            agendamento=agendamento_conflitante,
            servico=self.servico,
            servico_nome=self.servico.nome,
            preco_unitario=self.servico.valor,
            duracao_minutos=30,
        )
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_local.date().isoformat(),
                'data': data_local.strftime('%Y-%m-%dT%H:%M'),
                'servicos': [self.servico.pk],
            },
            instance=self.agendamento,
            usuario=self.cliente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)

    def test_admin_altera_status_e_volta_para_data_selecionada(self):
        admin = Usuario.objects.create_user(
            username='admin-agendamento@example.com',
            email='admin-agendamento@example.com',
            nome='Admin Agendamento',
            password='Strong-Admin-Password!2026',
            is_staff=True,
        )
        self.client.force_login(admin)
        data = timezone.localtime(self.agendamento.data).date().isoformat()

        response = self.client.post(
            reverse('alterar_status_agendamento', args=[self.agendamento.pk]),
            {'status': Agendamento.StatusChoices.CONFIRMADO, 'data': data},
        )

        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.StatusChoices.CONFIRMADO)
        self.assertRedirects(
            response,
            f"{reverse('agendamentos')}?data={data}",
        )

    def test_alteracao_de_status_rejeita_valor_invalido(self):
        admin = Usuario.objects.create_user(
            username='admin-status@example.com',
            email='admin-status@example.com',
            nome='Admin Status',
            password='Strong-Admin-Password!2026',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('alterar_status_agendamento', args=[self.agendamento.pk]),
            {'status': 'Status inválido'},
        )

        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.status, Agendamento.StatusChoices.PENDENTE)
        self.assertRedirects(response, reverse('agendamentos'))

    def test_cliente_nao_pode_alterar_status(self):
        self.client.force_login(self.cliente)

        response = self.client.post(
            reverse('alterar_status_agendamento', args=[self.agendamento.pk]),
            {'status': Agendamento.StatusChoices.CONFIRMADO},
        )

        self.agendamento.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.agendamento.status, Agendamento.StatusChoices.PENDENTE)

    def test_colaborador_pode_alterar_status(self):
        colaborador = Usuario.objects.create_user(
            username='colaborador-status@example.com',
            email='colaborador-status@example.com',
            nome='Colaborador Status',
            password='Strong-Collaborator-Password!2026',
            is_staff=True,
            is_colaborador=True,
        )
        self.client.force_login(colaborador)
        data = timezone.localtime(self.agendamento.data).date().isoformat()

        response = self.client.post(
            reverse('alterar_status_agendamento', args=[self.agendamento.pk]),
            {'status': Agendamento.StatusChoices.CONFIRMADO, 'data': data},
        )

        self.agendamento.refresh_from_db()
        self.assertRedirects(
            response,
            f"{reverse('agendamentos')}?data={data}",
        )
        self.assertEqual(self.agendamento.status, Agendamento.StatusChoices.CONFIRMADO)


class CadastroCompostoTests(TestCase):
    def test_cadastro_exibe_regras_de_senha_de_forma_resumida(self):
        response = self.client.get(reverse('cadastro'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Mínimo de 8 caracteres. Evite dados pessoais e senhas comuns; não use apenas números.',
        )

    def test_cadastro_preserva_nome_do_tutor_e_do_pet_separadamente(self):
        response = self.client.post(
            reverse('cadastro'),
            {
                'usuario-nome': 'Tutor Exemplo',
                'usuario-email': 'tutor-exemplo@example.com',
                'usuario-telefone': '(11) 91234-5678',
                'usuario-senha': 'Strong-Registration-Password!2026',
                'usuario-confirmar_senha': 'Strong-Registration-Password!2026',
                'usuario-aceita_regulamento': 'on',
                'endereco-cep': '01001-000',
                'endereco-logradouro': 'Praça da Sé',
                'endereco-numero': '1',
                'endereco-complemento': '',
                'endereco-bairro': 'Sé',
                'endereco-cidade': 'São Paulo',
                'endereco-uf': 'SP',
                'pet-nome': 'Chuchu',
                'pet-data_de_nascimento': '2021-02-01',
                'pet-raca': 'SRD',
                'pet-porte': 'Pequeno',
                'pet-observacao': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        usuario = Usuario.objects.get(email='tutor-exemplo@example.com')
        pet = Pet.objects.get(usuario=usuario)
        self.assertEqual(usuario.nome, 'Tutor Exemplo')
        self.assertEqual(pet.nome, 'Chuchu')

    def test_cadastro_rejeita_sem_aceite_do_regulamento(self):
        response = self.client.post(reverse('cadastro'), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Regulamento Geral')
        self.assertContains(response, 'name="usuario-aceita_regulamento"')
        self.assertContains(response, 'Li e concordo com o regulamento.')
        self.assertIn(
            'aceita_regulamento', response.context['form_usuario'].errors
        )
        self.assertEqual(Usuario.objects.count(), 0)


class PasswordChangeCsrfTests(TestCase):
    def test_logout_funciona_apos_alterar_senha_sem_recarregar_manualmente(self):
        usuario = Usuario.objects.create_user(
            username='admin-csrf@example.com',
            email='admin-csrf@example.com',
            nome='Admin CSRF',
            password='Original-Strong-Password!2026',
            is_staff=True,
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(usuario)

        perfil = client.get(reverse('perfil'))
        token_senha = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"', perfil.content
        ).group(1).decode()
        csrf_antes = client.cookies['csrftoken'].value
        resposta = client.post(
            reverse('perfil'),
            {
                'csrfmiddlewaretoken': token_senha,
                'old_password': 'Original-Strong-Password!2026',
                'new_password1': 'Changed-Strong-Password!2026',
                'new_password2': 'Changed-Strong-Password!2026',
                'btn_alterar_senha': '1',
            },
            follow=True,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(client.cookies['csrftoken'].value, csrf_antes)

        resposta_logout = client.post(
            reverse('logout'), {'csrfmiddlewaretoken': token_senha}
        )

        self.assertRedirects(resposta_logout, reverse('login'))


class SolicitacaoTransporteTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='transporte-cliente@example.com',
            email='transporte-cliente@example.com',
            nome='Cliente Transporte',
            password='Strong-Transport-Password!2026',
        )
        self.endereco = Endereco.objects.create(
            cep='01001-000',
            logradouro='Praça da Sé',
            numero='1',
            bairro='Sé',
            cidade='São Paulo',
            uf='SP',
        )
        self.cliente.endereco = self.endereco
        self.cliente.save(update_fields=['endereco'])
        self.pet = Pet.objects.create(
            nome='Rex Transporte',
            data_de_nascimento=date(2021, 1, 15),
            raca='SRD',
            porte='Médio',
            usuario=self.cliente,
        )
        self.colaborador = Usuario.objects.create_user(
            username='transporte-colaborador@example.com',
            email='transporte-colaborador@example.com',
            nome='Colaborador Transporte',
            password='Strong-Transport-Collaborator!2026',
            is_staff=True,
            is_colaborador=True,
        )
        data_atendimento = timezone.localdate() + timedelta(days=2)
        self.agendamento = Agendamento.objects.create(
            usuario=self.cliente,
            pet=self.pet,
            colaborador=self.colaborador,
            data=timezone.make_aware(
                datetime.combine(data_atendimento, time(14))
            ),
        )
        self.admin = Usuario.objects.create_user(
            username='transporte-admin@example.com',
            email='transporte-admin@example.com',
            nome='Admin Transporte',
            password='Strong-Transport-Admin!2026',
            is_staff=True,
        )

    def _dados_solicitacao(self, horario=None):
        if horario is None:
            horario = timezone.localtime(self.agendamento.data) - timedelta(hours=1)
        return {
            'endereco_retirada': 'Rua Nova, 10, Centro, São Paulo/SP',
            'horario_preferido': horario.strftime('%Y-%m-%dT%H:%M'),
            'observacoes': 'Ligar ao chegar.',
            'politica_aceita': 'on',
        }

    def test_usuario_solicita_transporte_com_endereco_editavel(self):
        self.client.force_login(self.cliente)
        resposta_get = self.client.get(
            reverse('solicitar_transporte', args=[self.agendamento.pk])
        )

        self.assertEqual(resposta_get.status_code, 200)
        self.assertIn(
            'Praça da Sé, 1 - Sé, São Paulo/SP, CEP 01001-000',
            resposta_get.context['form']['endereco_retirada'].value(),
        )

        resposta_post = self.client.post(
            reverse('solicitar_transporte', args=[self.agendamento.pk]),
            self._dados_solicitacao(),
        )

        data_agendamento = timezone.localtime(self.agendamento.data).date().isoformat()
        self.assertRedirects(
            resposta_post,
            f"{reverse('agendamentos')}?data={data_agendamento}",
        )
        solicitacao = SolicitacaoTransporte.objects.get(
            agendamento=self.agendamento
        )
        self.assertEqual(solicitacao.status, SolicitacaoTransporte.StatusChoices.SOLICITADO)
        self.assertEqual(
            solicitacao.endereco_retirada,
            'Rua Nova, 10, Centro, São Paulo/SP',
        )

    def test_nao_permite_retirada_depois_do_agendamento(self):
        self.client.force_login(self.cliente)
        horario_invalido = timezone.localtime(self.agendamento.data) + timedelta(minutes=1)

        resposta = self.client.post(
            reverse('solicitar_transporte', args=[self.agendamento.pk]),
            self._dados_solicitacao(horario=horario_invalido),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn('horario_preferido', resposta.context['form'].errors)
        self.assertFalse(
            SolicitacaoTransporte.objects.filter(
                agendamento=self.agendamento
            ).exists()
        )

    def test_solicitacao_exige_aceite_da_politica(self):
        self.client.force_login(self.cliente)
        dados = self._dados_solicitacao()
        dados.pop('politica_aceita')

        resposta = self.client.post(
            reverse('solicitar_transporte', args=[self.agendamento.pk]),
            dados,
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn('politica_aceita', resposta.context['form'].errors)
        self.assertFalse(
            SolicitacaoTransporte.objects.filter(
                agendamento=self.agendamento
            ).exists()
        )

    def test_usuario_nao_pode_solicitar_transporte_para_agendamento_alheio(self):
        outro_cliente = Usuario.objects.create_user(
            username='outro-transporte@example.com',
            email='outro-transporte@example.com',
            nome='Outro Cliente',
            password='Strong-Other-Transport!2026',
        )
        outro_pet = Pet.objects.create(
            nome='Outro Pet',
            data_de_nascimento=date(2020, 5, 1),
            raca='SRD',
            porte='Pequeno',
            usuario=outro_cliente,
        )
        agendamento_alheio = Agendamento.objects.create(
            usuario=outro_cliente,
            pet=outro_pet,
            data=self.agendamento.data,
        )
        self.client.force_login(self.cliente)

        resposta = self.client.get(
            reverse('solicitar_transporte', args=[agendamento_alheio.pk])
        )

        self.assertEqual(resposta.status_code, 404)

    def test_equipe_confirma_horario_e_taxa(self):
        solicitacao = SolicitacaoTransporte.objects.create(
            agendamento=self.agendamento,
            endereco_retirada='Rua Nova, 10',
            horario_preferido=timezone.localtime(self.agendamento.data) - timedelta(hours=1),
            politica_aceita=True,
        )
        self.client.force_login(self.admin)
        horario_confirmado = timezone.localtime(self.agendamento.data) - timedelta(minutes=45)

        resposta = self.client.post(
            reverse('editar_solicitacao_transporte', args=[solicitacao.pk]),
            {
                'status': SolicitacaoTransporte.StatusChoices.CONFIRMADO,
                'horario_confirmado': horario_confirmado.strftime('%Y-%m-%dT%H:%M'),
                'taxa': '25.00',
            },
        )

        self.assertRedirects(resposta, reverse('gerenciar_transportes'))
        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, SolicitacaoTransporte.StatusChoices.CONFIRMADO)
        self.assertEqual(solicitacao.taxa, Decimal('25.00'))
        self.assertEqual(solicitacao.horario_confirmado, horario_confirmado)

    def test_equipe_nao_confirma_sem_horario_e_taxa(self):
        solicitacao = SolicitacaoTransporte.objects.create(
            agendamento=self.agendamento,
            endereco_retirada='Rua Nova, 10',
            horario_preferido=timezone.localtime(self.agendamento.data) - timedelta(hours=1),
            politica_aceita=True,
        )
        self.client.force_login(self.admin)

        resposta = self.client.post(
            reverse('editar_solicitacao_transporte', args=[solicitacao.pk]),
            {
                'status': SolicitacaoTransporte.StatusChoices.CONFIRMADO,
                'horario_confirmado': '',
                'taxa': '',
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn('horario_confirmado', resposta.context['form'].errors)
        self.assertIn('taxa', resposta.context['form'].errors)
        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, SolicitacaoTransporte.StatusChoices.SOLICITADO)

    def test_cliente_nao_acessa_gerenciamento_de_transportes(self):
        self.client.force_login(self.cliente)

        resposta = self.client.get(reverse('gerenciar_transportes'))

        self.assertEqual(resposta.status_code, 302)

    def test_edicao_nao_antecipa_atendimento_para_depois_da_retirada(self):
        servico = Servico.objects.create(
            nome='Banho para transporte',
            valor=Decimal('30.00'),
            duracao_minutos=30,
        )
        for dia_semana in range(7):
            HorarioFuncionamento.objects.create(
                dia_semana=dia_semana,
                fechado=False,
                hora_abertura=time(9),
                hora_fechamento=time(18),
            )
        horario_retirada = timezone.localtime(self.agendamento.data).replace(
            hour=13, minute=30
        )
        SolicitacaoTransporte.objects.create(
            agendamento=self.agendamento,
            endereco_retirada='Rua Nova, 10',
            horario_preferido=horario_retirada,
            politica_aceita=True,
        )
        data_local = timezone.localtime(self.agendamento.data)
        form = AgendamentoForm(
            data={
                'pet': self.pet.pk,
                'colaborador': self.colaborador.pk,
                'data_dia': data_local.date().isoformat(),
                'data': data_local.strftime('%Y-%m-%dT13:00'),
                'servicos': [servico.pk],
            },
            instance=self.agendamento,
            usuario=self.cliente,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)
