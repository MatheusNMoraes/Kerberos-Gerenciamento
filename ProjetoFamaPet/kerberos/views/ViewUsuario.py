from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms.FormUsuario import UsuarioForm
from ..models.usuario import Usuario

def listar_clientes(request):
    usuarios = Usuario.objects.all()
    contexto = {'usuarios': usuarios}
    return render(request, 'usuario/clientes.html', contexto)

def criar_cliente(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('clientes')
    else:
        form = UsuarioForm()
    return render(request, 'usuario/criar_cliente.html', {'form': form})

def editar_cliente(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('clientes')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'usuario/cliente_form.html', {'form': form})

def deletar_cliente(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Cliente removido com sucesso!')
        return redirect('clientes')
    return render(request, 'usuario/cliente_deletar.html', {'usuario': usuario})