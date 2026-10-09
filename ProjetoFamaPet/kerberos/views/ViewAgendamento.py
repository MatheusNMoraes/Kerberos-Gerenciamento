from datetime import datetime
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from kerberos.forms.FormAgendamento import AgendamentoForm
from kerberos.models.agendamento import Agendamento, ItemAgendamento


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

    agendamentos_manha = [a for a in agendamentos_lista if 9 <= a.data.hour < 12]
    agendamentos_tarde = [a for a in agendamentos_lista if 13 <= a.data.hour < 18]
    agendamentos_noite = [a for a in agendamentos_lista if 19 <= a.data.hour <= 21]

    contexto = {
        'agendamentos': agendamentos_lista,
        'data_selecionada': data_selecionada,
        'agendamentos_manha': agendamentos_manha,
        'agendamentos_tarde': agendamentos_tarde,
        'agendamentos_noite': agendamentos_noite,
    }

    return render(request, 'agendamento/agendamentos.html', contexto)


@login_required
@transaction.atomic
def criar_agendamento(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, usuario=request.user)
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
                ItemAgendamento.objects.create(
                    agendamento=agendamento,
                    servico=servico,
                    servico_nome=servico.nome,
                    preco_unitario=servico.valor,
                    duracao_minutos=servico.duracao_minutos
                )

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
        if form.is_valid():
            agendamento = form.save(commit=False)
            if request.user.is_staff:
                agendamento.usuario = form.cleaned_data['pet'].usuario
            agendamento.save()

            # Recria os itens com os novos preços/serviços
            agendamento.itens.all().delete()
            servicos_selecionados = form.cleaned_data['servicos']
            for servico in servicos_selecionados:
                ItemAgendamento.objects.create(
                    agendamento=agendamento,
                    servico=servico,
                    servico_nome=servico.nome,
                    preco_unitario=servico.valor,
                    duracao_minutos=servico.duracao_minutos
                )

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