from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms.FormUsuario import UsuarioForm
from ..models import Usuario

def perfil(request):
    
    usuario = Usuario.objects.first()
    
    if not usuario:
        messages.error(request, 'Nenhum usuário cadastrado.')
        return redirect('home') # Use o nome da URL mapeada no urls.py, ex: name='home'
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil') # Use o nome da URL desta página, ex: name='perfil'
    else:
        form = UsuarioForm(instance=usuario)

    context = {
        'form': form,
    }
    return render(request, 'perfil/perfil.html', context)