from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Agendamento

def relatorio(request):
    relatorios = Agendamento.objects.prefetch_related('servicos').select_related('usuario', 'pet')
    faturamento = sum(relatorios.valorTotal for relatorio in relatorios)
    contexto = {"relatorio": relatorios,'faturamento': faturamento,}
    return render(request, 'relatorio/relatorio.html', contexto)