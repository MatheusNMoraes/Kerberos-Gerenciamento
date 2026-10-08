from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from ..forms.FormAgendamento import AgendamentoForm
from ..models import Agendamento

def agendamentos(request):
    data_str = request.GET.get('data')

    if data_str:
        try:
            data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            data_selecionada = timezone.now().date()
    else:
        data_selecionada = timezone.now().date()

    agendamentos_qs = (
        Agendamento.objects
        .prefetch_related('servicos')
        .select_related('usuario', 'pet')
        .filter(data__date=data_selecionada)
        .order_by('data')
    )

    contexto = {
        'agendamentos': agendamentos_qs,
        'data_selecionada': data_selecionada,
        'agendamentos_manha': agendamentos_qs.filter(data__time__gte='09:00', data__time__lt='12:00'),
        'agendamentos_tarde': agendamentos_qs.filter(data__time__gte='13:00', data__time__lt='18:00'),
        'agendamentos_noite': agendamentos_qs.filter(data__time__gte='19:00', data__time__lte='21:00'),
    }

    return render(request, 'agendamento/agendamentos.html', contexto)

def criar_agendamento(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agendamento cadastrado com sucesso!')
            return redirect('agendamentos')
        messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = AgendamentoForm()

    return render(request, 'agendamento/criar_agendamento.html', {'form': form})

def editar_agendamento(request, pk):
    try:
        agendamento = Agendamento.objects.get(pk=pk)
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado ou já foi removido.')
        return redirect('agendamentos')

    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agendamento atualizado com sucesso!')
            return redirect('agendamentos')
        messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = AgendamentoForm(instance=agendamento)

    return render(request, 'agendamento/editar_agendamento.html', {
        'form': form,
        'agendamento': agendamento
    })

def deletar_agendamento(request, pk):
    try:
        agendamento = Agendamento.objects.get(pk=pk)
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado ou já foi removido.')
        return redirect('agendamentos')

    if request.method == 'POST':
        detalhe = f"{agendamento.pet.nome} ({agendamento.data.strftime('%d/%m/%Y às %H:%H') if agendamento.data else ''})"
        agendamento.delete()
        messages.success(request, f'Agendamento de {detalhe} foi excluído com sucesso!')
        return redirect('agendamentos')

    return render(request, 'agendamento/deletar_agendamento.html', {
        'agendamento': agendamento
    })