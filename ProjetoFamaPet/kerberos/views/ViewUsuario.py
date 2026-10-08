from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q
from django.contrib import messages

from ..forms.FormUsuario import UsuarioForm
from ..forms.FormEndereco import EnderecoForm
from ..models.usuario import Usuario


@login_required
def listar_clientes(request):
    query = request.GET.get('q', '').strip()
    usuarios = Usuario.objects.select_related('endereco').all()

    if query:
        usuarios = usuarios.filter(
            Q(nome__icontains=query)
        )

    contexto = {'usuarios': usuarios}
    return render(request, 'usuario/clientes.html', contexto)


@login_required
def criar_cliente(request):
    if request.method == 'POST':
        usuario_form = UsuarioForm(request.POST)
        endereco_form = EnderecoForm(request.POST)

        if usuario_form.is_valid() and endereco_form.is_valid():
            try:
                with transaction.atomic():
                    endereco = endereco_form.save()
                    
                    usuario = usuario_form.save(commit=False)
                    usuario.endereco = endereco
                    usuario.save()

                messages.success(request, 'Cliente e Endereço cadastrados com sucesso!')
                return redirect('listar_clientes')

            except Exception as e:
                messages.error(request, f'Erro inesperado ao salvar no banco de dados: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija os erros apontados no formulário abaixo.')
    else:
        usuario_form = UsuarioForm()
        endereco_form = EnderecoForm()

    contexto = {
        'form': usuario_form,
        'endereco_form': endereco_form,
        'titulo': 'Cadastrar Novo Cliente'
    }
    return render(request, 'usuario/cliente_form.html', contexto)


@login_required
def editar_cliente(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    endereco = usuario.endereco

    if request.method == 'POST':
        usuario_form = UsuarioForm(request.POST, instance=usuario)
        endereco_form = EnderecoForm(request.POST, instance=endereco)

        if usuario_form.is_valid() and endereco_form.is_valid():
            try:
                with transaction.atomic():
                    novo_endereco = endereco_form.save()
                    
                    usuario_editado = usuario_form.save(commit=False)
                    usuario_editado.endereco = novo_endereco
                    usuario_editado.save()

                messages.success(request, f'Dados de {usuario_editado.nome} atualizados com sucesso!')
                return redirect('listar_clientes')

            except Exception as e:
                messages.error(request, f'Erro ao atualizar registro: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija os erros apontados no formulário abaixo.')
    else:
        usuario_form = UsuarioForm(instance=usuario)
        endereco_form = EnderecoForm(instance=endereco)

    contexto = {
        'form': usuario_form,
        'endereco_form': endereco_form,
        'usuario': usuario,
        'titulo': 'Editar Cliente'
    }
    return render(request, 'usuario/cliente_form.html', contexto)


@login_required
@require_POST
def deletar_cliente(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    endereco = usuario.endereco
    
    with transaction.atomic():
        usuario.delete()
        if endereco:
            endereco.delete()

    messages.success(request, 'Cliente removido com sucesso!')
    return redirect('listar_clientes')