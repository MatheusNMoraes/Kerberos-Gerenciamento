from datetime import date, datetime
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from kerberos.forms.FormAgendamento import AgendamentoForm
from kerberos.decorators import operador_required
from kerberos.models.agendamento import Agendamento, ItemAgendamento
from kerberos.models.servico import Servico
from kerberos.services.disponibilidade import (
    bloquear_configuracao_dia,
    horarios_disponiveis,
)


def _criar_item_agendamento(agendamento, servico):
    ItemAgendamento.objects.create(
        agendamento=agendamento,
        servico=servico,
        servico_nome=servico.nome,
        preco_unitario=servico.valor,
        duracao_minutos=servico.duracao_minutos,
    )


def _bloquear_data_do_post(request):
    try:
        data_selecionada = date.fromisoformat(request.POST.get("data_dia", ""))
    except ValueError:
        return
    bloquear_configuracao_dia(data_selecionada)


@login_required
def agendamentos(request):
    data_str = request.GET.get('data')

    if data_str:
        try:
            data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            data_selecionada = timezone.now().date()
    else:
        data_selecionada = timezone.now().date()

    # Staff/Admin vê a agenda completa do petshop; Cliente vê apenas os seus
    if request.user.is_staff:
        base_qs = Agendamento.objects.all()
    else:
        base_qs = Agendamento.objects.filter(usuario=request.user)

    agendamentos_lista = list(
        base_qs
        .prefetch_related('itens')
        .select_related('usuario', 'pet')
        .filter(data__date=data_selecionada)
        .order_by('data')
    )

    contexto = {
        'agendamentos': agendamentos_lista,
        'data_selecionada': data_selecionada,
        'status_choices': Agendamento.StatusChoices.choices,
    }

    return render(request, 'agendamento/agendamentos.html', contexto)


@login_required
def horarios_disponiveis_json(request):
    try:
        data_selecionada = date.fromisoformat(request.GET.get("data", ""))
    except ValueError:
        return JsonResponse({"horarios": []})

    ids_servicos = request.GET.getlist("servicos")
    if not ids_servicos or any(not item.isdigit() for item in ids_servicos):
        return JsonResponse({"horarios": []})

    agendamento = None
    agendamento_id = request.GET.get("agendamento_id")
    if agendamento_id and agendamento_id.isdigit():
        queryset = Agendamento.objects.all()
        if not request.user.is_staff:
            queryset = queryset.filter(usuario=request.user)
        agendamento = get_object_or_404(queryset, pk=agendamento_id)

    servicos = Servico.objects.filter(pk__in=ids_servicos, ativo=True)
    if agendamento:
        servicos = Servico.objects.filter(
            Q(ativo=True) | Q(itens_agendados__agendamento=agendamento),
            pk__in=ids_servicos,
        ).distinct()
    servicos = list(servicos)
    if len({servico.pk for servico in servicos}) != len(set(ids_servicos)):
        return JsonResponse({"horarios": []})

    duracao = sum(servico.duracao_minutos for servico in servicos)
    horarios = horarios_disponiveis(
        data_selecionada,
        duracao,
        agendamento_id=agendamento.pk if agendamento else None,
    )
    return JsonResponse({
        "horarios": [
            {
                "valor": timezone.localtime(horario).strftime("%Y-%m-%dT%H:%M"),
                "rotulo": timezone.localtime(horario).strftime("%H:%M"),
            }
            for horario in horarios
        ],
    })


@operador_required
@require_POST
def alterar_status_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    novo_status = request.POST.get('status')

    if novo_status not in Agendamento.StatusChoices.values:
        messages.error(request, 'O status selecionado não é válido.')
    else:
        agendamento.status = novo_status
        agendamento.save(update_fields=['status', 'atualizado_em'])
        messages.success(request, 'Status do agendamento atualizado com sucesso.')

    data_str = request.POST.get('data', '')
    try:
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return redirect('agendamentos')

    return redirect(
        f"{reverse('agendamentos')}?{urlencode({'data': data_selecionada.isoformat()})}"
    )


@login_required
@transaction.atomic
def criar_agendamento(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, usuario=request.user)
        _bloquear_data_do_post(request)
        if form.is_valid():
            agendamento = form.save(commit=False)
            
            # Vincula ao tutor (se for Admin) ou ao usuário comum
            if request.user.is_staff:
                agendamento.usuario = form.cleaned_data['pet'].usuario
            else:
                agendamento.usuario = request.user

            agendamento.save()

            # Congela os serviços nos itens
            servicos_selecionados = form.cleaned_data['servicos']
            for servico in servicos_selecionados:
                _criar_item_agendamento(agendamento, servico)

            messages.success(request, 'Agendamento cadastrado com sucesso!')
            return redirect('agendamentos')
        messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = AgendamentoForm(usuario=request.user)

    return render(request, 'agendamento/agendamento_form.html', {
        'form': form,
        'titulo_pagina': 'Novo Agendamento',
        'botao_texto': 'Confirmar Agendamento',
    })


@login_required
@transaction.atomic
def editar_agendamento(request, pk):
    if request.user.is_staff:
        agendamento = get_object_or_404(Agendamento, pk=pk)
    else:
        agendamento = get_object_or_404(Agendamento, pk=pk, usuario=request.user)

    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento, usuario=request.user)
        _bloquear_data_do_post(request)
        if form.is_valid():
            agendamento = form.save(commit=False)
            if request.user.is_staff:
                agendamento.usuario = form.cleaned_data['pet'].usuario
            agendamento.save()

            itens_existentes = {
                item.servico_id: item for item in agendamento.itens.all()
            }
            servicos_selecionados = {
                servico.pk: servico for servico in form.cleaned_data['servicos']
            }

            for servico_id, item in itens_existentes.items():
                if servico_id not in servicos_selecionados:
                    item.delete()

            for servico_id, servico in servicos_selecionados.items():
                if servico_id in itens_existentes:
                    continue
                _criar_item_agendamento(agendamento, servico)

            messages.success(request, 'Agendamento atualizado com sucesso!')
            return redirect('agendamentos')
        messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = AgendamentoForm(instance=agendamento, usuario=request.user)

    return render(request, 'agendamento/agendamento_form.html', {
        'form': form,
        'agendamento': agendamento,
        'titulo_pagina': 'Editar Agendamento',
        'botao_texto': 'Salvar Alterações',
    })


@login_required
def deletar_agendamento(request, pk):
    if request.user.is_staff:
        agendamento = get_object_or_404(Agendamento, pk=pk)
    else:
        agendamento = get_object_or_404(Agendamento, pk=pk, usuario=request.user)

    if request.method == 'POST':
        data_fmt = agendamento.data.strftime('%d/%m/%Y às %H:%M') if agendamento.data else ''
        detalhe = f"{agendamento.pet.nome} ({data_fmt})"
        agendamento.delete()
        messages.success(request, f'Agendamento de {detalhe} foi excluído com sucesso!')
        return redirect('agendamentos')

    return render(request, 'agendamento/deletar_agendamento.html', {
        'agendamento': agendamento
    })