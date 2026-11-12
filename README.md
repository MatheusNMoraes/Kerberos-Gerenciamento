# Kerberos-Gerenciamento

O Kerberos é uma plataforma de gestão focada no mercado pet, desenvolvida para simplificar o agendamento de banho e tosa, controle de horários e cadastro de clientes e pets. Ideal para petshops.

  **Funcionalidades**

Painel do Administrador (Petshop)
- Agenda Centralizada: Controle visual de horários, cliente e serviços.
- Gestão de Clientes e Pets: Histórico de atendimento, preferências informações de saúde (vacinas, alergias).
- Relatórios: Controle de fluxo de caixa e serviços realizados.

Portal do Cliente (Tutor)
- Agendamento Online: Escolha de data, horário, serviço e profissional em tempo real. 
- Meus Pets: Cadastro de múltiplos pets com foto, raça, idade e restrições.
- Histórico de Serviços: Visualização de todos os serviços agendados no passado ou futuros.


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
