from datetime import datetime
from django.db.models import Sum, Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from kerberos.models.agendamento import Agendamento, ItemAgendamento
from kerberos.models.pet import Pet


@login_required
def relatorio(request):
    if request.user.is_colaborador:
        raise PermissionDenied

    agora = timezone.now()
    hoje = timezone.localdate(agora)
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    pet_id = request.GET.get('pet_id')

    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else hoje.replace(day=1)
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date() if data_fim_str else hoje
    except ValueError:
        data_inicio = hoje.replace(day=1)
        data_fim = hoje

    if request.user.is_staff:
        agendamentos_qs = Agendamento.objects.all()
    else:
        agendamentos_qs = Agendamento.objects.filter(usuario=request.user)

    agendamentos_qs = agendamentos_qs.filter(
        data__date__gte=data_inicio,
        data__date__lte=data_fim
    ).prefetch_related('itens').select_related('usuario', 'pet').order_by('-data')

    if pet_id:
        agendamentos_qs = agendamentos_qs.filter(pet_id=pet_id)

    agendamentos_list = list(agendamentos_qs)

    concluidos_realizados = [
        agendamento
        for agendamento in agendamentos_list
        if (
            agendamento.status == Agendamento.StatusChoices.CONCLUIDO
            and agendamento.data <= agora
        )
    ]
    total_faturamento = sum(a.valor_total for a in concluidos_realizados)
    total_atendimentos = len(concluidos_realizados)
    ticket_medio = (total_faturamento / total_atendimentos) if total_atendimentos > 0 else 0

    itens_qs = ItemAgendamento.objects.filter(agendamento__in=concluidos_realizados)
    ranking_servicos = (
        itens_qs.values('servico_nome')
        .annotate(
            qtd=Count('id'),
            total_gerado=Sum('preco_unitario')
        )
        .order_by('-qtd')[:5]
    )

    if request.user.is_staff:
        pets_filtro = Pet.objects.all().order_by('nome')
    else:
        pets_filtro = Pet.objects.filter(usuario=request.user).order_by('nome')

    contexto = {
        'agendamentos': agendamentos_list,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'pet_id_selecionado': int(pet_id) if pet_id and pet_id.isdigit() else None,
        'pets_filtro': pets_filtro,
        'total_faturamento': total_faturamento,
        'total_atendimentos': total_atendimentos,
        'ticket_medio': ticket_medio,
        'ranking_servicos': ranking_servicos,
    }

    return render(request, 'relatorio/relatorio.html', contexto)