# Revisão de segurança e lógica

## Escopo

Revisão estática do projeto Django, cobrindo configurações, rotas, autenticação,
autorização, views, formulários, modelos, serviços e templates. A aplicação em
execução e a infraestrutura de implantação não foram avaliadas.

## Achados

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| 1 | 🟡 MEDIUM | `kerberos/forms/FormAgendamento.py` | 100-107 | Ao editar um agendamento e manter a mesma data/hora, a validação retorna antes de recalcular a duração. Adicionar um serviço pode fazer o atendimento ultrapassar o expediente/pausa ou conflitar com outro agendamento. | 9/10 |
| 2 | 🟡 MEDIUM | `kerberos/views/ViewCadastrar.py` | 22-25 | O cadastro atribui `endereco.usuario`, mas a relação está em `Usuario.endereco`; o endereço é salvo sem ser vinculado ao tutor. | 10/10 |
| 3 | ⚪ LOW | `FamaPet/settings.py` | 12, 119-122 | Com `DEBUG=False`, o redirecionamento HTTPS é ativado. Testes e execução local via HTTP recebem redirecionamentos; a suíte atual terminou com 27 falhas e 2 erros. Use HTTPS ou desative o redirecionamento no ambiente de testes. | 10/10 |

## Validação

- `python manage.py check`: passou sem problemas.
- `python manage.py test`: 50 testes executados; 27 falhas e 2 erros, associados
  aos redirecionamentos HTTPS em requisições HTTP.

O revisor especializado não identificou vulnerabilidades de segurança
verificáveis nas áreas inspecionadas.
