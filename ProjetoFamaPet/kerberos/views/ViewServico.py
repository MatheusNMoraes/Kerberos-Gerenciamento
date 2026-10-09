from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from ..models.servico import Servico
from ..forms.FormServico import ServicoForm


@staff_member_required
def listar_servicos(request):
    """Lista todos os serviços cadastrados no sistema."""
    servicos = Servico.objects.all().order_by('nome')
    return render(request, 'servicos/listar_servicos.html', {'servicos': servicos})


@staff_member_required
def salvar_servico(request, pk=None):
    """View reutilizável para Criar e Editar Serviços."""
    if pk:
        servico = get_object_or_404(Servico, pk=pk)
        titulo_pagina = "Editar Serviço"
        botao_texto = "Salvar Alterações"
    else:
        servico = None
        titulo_pagina = "Novo Serviço"
        botao_texto = "Cadastrar Serviço"

    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            form.save()
            msg = "Serviço atualizado com sucesso!" if pk else "Serviço cadastrado com sucesso!"
            messages.success(request, msg)
            return redirect('listar_servicos')
        messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = ServicoForm(instance=servico)

    return render(request, 'servicos/form_servico.html', {
        'form': form,
        'servico': servico,
        'titulo_pagina': titulo_pagina,
        'botao_texto': botao_texto
    })


@staff_member_required
def deletar_servico(request, pk):
    """Inativa ou deleta o serviço."""
    servico = get_object_or_404(Servico, pk=pk)

    if request.method == 'POST':
        nome = servico.nome
        # Se o serviço estiver vinculado a agendamentos anteriores, apenas inativamos
        if servico.itens_agendados.exists():
            servico.ativo = False
            servico.save()
            messages.warning(request, f'O serviço "{nome}" foi desativado para novos agendamentos pois já possui histórico.')
        else:
            servico.delete()
            messages.success(request, f'O serviço "{nome}" foi excluído com sucesso!')
            
        return redirect('listar_servicos')

    return render(request, 'servicos/deletar_servico.html', {'servico': servico})