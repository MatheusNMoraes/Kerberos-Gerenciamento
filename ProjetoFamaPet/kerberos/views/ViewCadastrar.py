from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms.FormCadastro import CadastroForm
from ..forms.FormPet import PetForm
from ..models import Usuario
from ..models import Pet

def cadastrar_usuario(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Faça seu login.')
            return redirect('login')
    else:
        form = CadastroForm()
    
    return render(request, 'cadastro/cadastro.html', {'form': form})