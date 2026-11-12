from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from kerberos.decorators import operador_required
from kerberos.forms.FormTransporte import (
    GerenciarTransporteForm,
    SolicitacaoTransporteForm,
)
from kerberos.models.agendamento import Agendamento
from kerberos.models.transporte import SolicitacaoTransporte


def _redirecionar_para_data_agendamento(agendamento):
    data = timezone.localtime(agendamento.data).date().isoformat()
    return redirect(f"{reverse('agendamentos')}?data={data}")


@login_required
@transaction.atomic
def solicitar_transporte(request, agendamento_id):
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("usuario", "pet"),
        pk=agendamento_id,
        usuario=request.user,
    )
    if (
        agendamento.status
        not in (
            Agendamento.StatusChoices.PENDENTE,
            Agendamento.StatusChoices.CONFIRMADO,
        )
        or agendamento.data <= timezone.now()
    ):
        messages.error(
            request,
            "Só é possível solicitar transporte para agendamentos futuros ativos.",
        )
        return _redirecionar_para_data_agendamento(agendamento)

    if SolicitacaoTransporte.objects.filter(agendamento=agendamento).exists():
        messages.info(request, "Este agendamento já possui uma solicitação de transporte.")
        return _redirecionar_para_data_agendamento(agendamento)

    form = SolicitacaoTransporteForm(
        request.POST if request.method == "POST" else None,
        agendamento=agendamento,
        usuario=request.user,
    )
    if request.method == "POST" and form.is_valid():
        solicitacao = form.save(commit=False)
        solicitacao.agendamento = agendamento
        solicitacao.save()
        messages.success(
            request,
            "Solicitação enviada. A equipe confirmará o horário e a taxa.",
        )
        return _redirecionar_para_data_agendamento(agendamento)

    return render(
        request,
        "transporte/solicitar.html",
        {"form": form, "agendamento": agendamento},
    )


@operador_required
def gerenciar_transportes(request):
    solicitacoes = SolicitacaoTransporte.objects.select_related(
        "agendamento__usuario",
        "agendamento__pet",
    )
    return render(
        request,
        "transporte/lista.html",
        {"solicitacoes": solicitacoes},
    )


@operador_required
@transaction.atomic
def editar_solicitacao_transporte(request, pk):
    solicitacao = get_object_or_404(
        SolicitacaoTransporte.objects.select_related(
            "agendamento__usuario",
            "agendamento__pet",
        ),
        pk=pk,
    )
    form = GerenciarTransporteForm(
        request.POST if request.method == "POST" else None,
        instance=solicitacao,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Solicitação de transporte atualizada.")
        return redirect("gerenciar_transportes")

    return render(
        request,
        "transporte/editar.html",
        {"form": form, "solicitacao": solicitacao},
    )
