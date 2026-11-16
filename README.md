# Kerberos-Gerenciamento

O Kerberos é uma plataforma de gestão focada no mercado pet, desenvolvida para simplificar o agendamento de banho e tosa, controle de horários e cadastro de clientes e pets. Ideal para petshops.

  **Funcionalidades**

Painel do Administrador (Petshop)
- Agenda Centralizada: Controle visual de horários, cliente e serviços.
- Gestão de Clientes e Pets: Histórico de atendimento e informações dos pets.
- Relatórios: Controle de fluxo de caixa e serviços realizados.

Portal do Cliente (Tutor)
- Agendamento Online: Escolha de data, horário, serviço e profissional em tempo real. 
- Meus Pets: Cadastro de múltiplos pets com raça, idade e observações.
- Histórico de Serviços: Visualização de todos os serviços agendados no passado ou futuros.
- Escolha de Profissional: Seleção de um colaborador ativo ao agendar um atendimento.


**Tecnologias Utilizadas**

- Frontend: templates Django, Bootstrap e JavaScript
- Backend: Python/Django
- Banco de dados: SQLite no desenvolvimento e PostgreSQL na implantação Docker
- Hospedagem: Docker Compose; requer um proxy HTTPS externo

**Como Rodar o Projeto**

Requer Python 3.12 ou compatível com as dependências listadas em
`requirements.txt`.

### Windows (PowerShell)

```powershell
cd ProjetoFamaPet
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r ..\requirements.txt
Copy-Item .env.example .env
```

Se o PowerShell bloquear a ativação do ambiente virtual, libere scripts apenas
na sessão atual e tente ativar novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Gere uma chave secreta e configure `DJANGO_SECRET_KEY` no arquivo `.env`:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Depois, inicialize o banco e execute o servidor local, ainda dentro de `ProjetoFamaPet`:

```powershell
python manage.py migrate
python manage.py runserver
```

### Linux/macOS (Bash)

```bash
cd ProjetoFamaPet
python -m venv .venv
source .venv/bin/activate
python -m pip install -r ../requirements.txt
cp .env.example .env
```

Gere uma chave secreta e configure `DJANGO_SECRET_KEY` no arquivo `.env`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Depois, inicialize o banco e execute o servidor local, ainda dentro de `ProjetoFamaPet`:

```bash
python manage.py migrate
python manage.py runserver
```

## Teste de implantação no Render

Este projeto inclui um Blueprint em `render.yaml` para criar um serviço Django
e um banco PostgreSQL no Render:

1. Envie o repositório ao GitHub.
2. No Render, abra **Blueprints** e escolha **New Blueprint Instance**.
3. Conecte o repositório e aplique o Blueprint definido em `render.yaml`.
4. Quando o serviço estiver criado, abra a URL `.onrender.com` indicada no
   painel e teste o site, cadastro e login.

O Render fornece automaticamente `RENDER_EXTERNAL_HOSTNAME`; a aplicação usa
esse valor para `ALLOWED_HOSTS` e para a origem CSRF do endereço `.onrender.com`.
Se adicionar domínio próprio, configure também `ALLOWED_HOSTS` e
`CSRF_TRUSTED_ORIGINS` nas variáveis do serviço.

O arquivo `.python-version` fixa a linha Python 3.12 usada localmente e na CI,
evitando que o Render escolha uma versão incompatível por padrão.

**Limitações do plano gratuito:** o serviço web pode dormir após inatividade e
demorar para responder à primeira visita. O sistema de arquivos do serviço é
temporário, então arquivos enviados localmente não persistem. O PostgreSQL
gratuito expira após 30 dias. Use essa configuração apenas para teste e não
armazene dados reais de clientes.

O plano gratuito do Render bloqueia conexões SMTP de saída nas portas 25, 465
e 587. Para testar recuperação de senha, configure um provedor de e-mail que
ofereça SMTP em uma porta permitida (por exemplo, 2525); informe
`EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` e `DEFAULT_FROM_EMAIL`
nas variáveis do serviço. Até configurar o e-mail, não conte com o envio de
mensagens de recuperação.

No plano gratuito não há shell interativo no serviço. Para criar o primeiro
administrador, use a URL externa do banco exibida no painel do Render a partir
do seu computador. No terminal local, dentro de `ProjetoFamaPet`, defina
temporariamente `DATABASE_URL` com essa URL e `DJANGO_SECRET_KEY` com a chave
do serviço e execute:

```bash
python manage.py createsuperuser
```

Não salve a URL do banco nem a chave no repositório. Remova as variáveis do
terminal depois do comando.

O comando de inicialização executa as migrações antes de iniciar o servidor.
Isso é adequado para o serviço gratuito de instância única usado no teste; um
deploy escalado deve executar migrações em uma etapa de pré-deploy dedicada.

## Implantação com Docker

A configuração de produção usa Docker Compose, PostgreSQL e Gunicorn. O
Compose publica a aplicação apenas em `127.0.0.1:8000`; coloque um proxy
reverso com TLS na frente dela. Esse proxy deve encaminhar
`X-Forwarded-Proto: https` e não deve permitir que clientes externos acessem
diretamente a porta da aplicação.

1. Copie `.env.production.example` para `.env.production` na raiz do
   repositório. O arquivo real é ignorado pelo Git:

   ```bash
   cp .env.production.example .env.production
   ```

2. Preencha o domínio real em `ALLOWED_HOSTS` e
   `CSRF_TRUSTED_ORIGINS`; configure uma chave secreta e as credenciais do
   PostgreSQL e do SMTP. Gere uma chave Django com:

   ```bash
   cd ProjetoFamaPet
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   cd ..
   ```

   Gere a senha do banco com `openssl rand -hex 32`. Não reutilize credenciais
   de desenvolvimento nem comite `.env.production`. Mantenha
   `SECURE_HSTS_INCLUDE_SUBDOMAINS=False` e
   `SECURE_HSTS_PRELOAD=False` a menos que todos os subdomínios estejam
   permanentemente preparados para HTTPS.

3. Configure o proxy TLS para apontar a `http://127.0.0.1:8000` e definir
   `X-Forwarded-Proto` com o protocolo recebido do cliente. O Compose habilita
   `USE_X_FORWARDED_PROTO=True`; use esse ajuste somente porque a aplicação
   fica atrás desse proxy confiável.

4. Construa a imagem, suba o banco, aplique as migrações e inicie a aplicação:

   ```bash
   docker compose --env-file .env.production build
   docker compose --env-file .env.production up -d db
   docker compose --env-file .env.production run --rm web python manage.py migrate --noinput
   docker compose --env-file .env.production up -d web
   ```

   Os arquivos estáticos são coletados durante a construção da imagem e
   servidos pelo WhiteNoise. Crie o usuário administrador com:

   ```bash
   docker compose --env-file .env.production run --rm web python manage.py createsuperuser
   ```

O endpoint `/healthz/` verifica se o processo web está respondendo. Os dados
do PostgreSQL ficam no volume `postgres_data`; configure cópias de segurança
fora do servidor e teste periodicamente a restauração. O volume Docker, por
si só, não é uma estratégia de backup. Configure também monitoramento,
alertas e retenção de logs no provedor de hospedagem.

O GitHub Actions executa `check`, valida as migrações e roda os testes contra
PostgreSQL a cada push e pull request.

Para atualizar a aplicação, construa a nova imagem, aplique migrações de forma
controlada e recrie o serviço web. Antes de atender usuários reais, valide em
staging o fluxo de recuperação de senha por e-mail, os backups/restauração, o
HTTPS e o procedimento de rollback. Os dados pessoais de tutores e pets
exigem políticas operacionais de acesso, retenção e atendimento à LGPD.
