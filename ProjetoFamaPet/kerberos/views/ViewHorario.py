from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from kerberos.decorators import administrador_required
from kerberos.forms.FormHorario import ExcecaoHorarioForm, HorarioDiaForm
from kerberos.models.horario import DIAS_DA_SEMANA, ExcecaoHorario, HorarioFuncionamento


def _linhas_horario_semanal(request):
    existentes = {
        horario.dia_semana: horario
        for horario in HorarioFuncionamento.objects.all()
    }
    linhas = []
    for dia, nome in DIAS_DA_SEMANA:
        horario = existentes.get(dia)
        initial = {
            "fechado": horario.fechado if horario else True,
            "hora_abertura": horario.hora_abertura if horario else None,
            "hora_fechamento": horario.hora_fechamento if horario else None,
            "pausa_inicio": horario.pausa_inicio if horario else None,
            "pausa_fim": horario.pausa_fim if horario else None,
        }
        form = HorarioDiaForm(
            request.POST if request.method == "POST" and request.POST.get("acao") == "salvar_semana" else None,
            prefix=f"dia-{dia}",
            initial=initial,
        )
        linhas.append({"nome": nome, "form": form, "dia": dia})
    return linhas


def _render_disponibilidade(request, excecao_form=None):
    return render(
        request,
        "agendamento/disponibilidade.html",
        {
            "linhas_horarios": _linhas_horario_semanal(request),
            "excecao_form": excecao_form or ExcecaoHorarioForm(),
            "excecoes": ExcecaoHorario.objects.all(),
        },
    )


@login_required
def gerenciar_disponibilidade(request):
    if request.method == "POST" and request.POST.get("acao") == "salvar_semana":
        linhas = _linhas_horario_semanal(request)
        validacoes = [linha["form"].is_valid() for linha in linhas]
        if all(validacoes):
            with transaction.atomic():
                for linha in linhas:
                    dados = linha["form"].cleaned_data
                    HorarioFuncionamento.objects.update_or_create(
                        dia_semana=linha["dia"],
                        defaults={
                            "fechado": dados["fechado"],
                            "hora_abertura": dados["hora_abertura"] if not dados["fechado"] else None,
                            "hora_fechamento": dados["hora_fechamento"] if not dados["fechado"] else None,
                            "pausa_inicio": dados["pausa_inicio"] if not dados["fechado"] else None,
                            "pausa_fim": dados["pausa_fim"] if not dados["fechado"] else None,
                        },
                    )
            messages.success(request, "Horários semanais atualizados.")
            return redirect("gerenciar_disponibilidade")
        return _render_disponibilidade(request)

    if request.method == "POST" and request.POST.get("acao") == "criar_excecao":
        excecao_form = ExcecaoHorarioForm(request.POST)
        if excecao_form.is_valid():
            excecao_form.save()
            messages.success(request, "Exceção de horário cadastrada.")
            return redirect("gerenciar_disponibilidade")
        return _render_disponibilidade(request, excecao_form)

    return _render_disponibilidade(request)


@login_required
def editar_excecao_horario(request, pk):
    excecao = get_object_or_404(ExcecaoHorario, pk=pk)
    form = ExcecaoHorarioForm(request.POST or None, instance=excecao)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Exceção de horário atualizada.")
        return redirect("gerenciar_disponibilidade")
    return render(
        request,
        "agendamento/excecao_horario_form.html",
        {"form": form, "excecao": excecao},
    )


@login_required
@require_POST
def deletar_excecao_horario(request, pk):
    excecao = get_object_or_404(ExcecaoHorario, pk=pk)
    excecao.delete()
    messages.success(request, "Exceção de horário removida.")
    return redirect("gerenciar_disponibilidade")