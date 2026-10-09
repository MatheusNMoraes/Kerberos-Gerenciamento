from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages

from ..forms.FormUsuario import UsuarioForm
from ..forms.FormEndereco import EnderecoForm 
from ..forms.FormPet import PetForm


@transaction.atomic
def cadastrar_usuario(request):
    if request.method == 'POST':
        form_usuario = UsuarioForm(request.POST)
        form_endereco = EnderecoForm(request.POST)
        form_pet = PetForm(request.POST, request.FILES)  # request.FILES se o pet tiver foto

        if form_usuario.is_valid() and form_endereco.is_valid() and form_pet.is_valid():
            # 1. Salva o Usuário (Garante is_staff=False por padrão e gera a senha com hash)
            usuario = form_usuario.save(commit=False)
            usuario.is_staff = False
            
            # Se o UsuarioForm usar senha em texto puro, converta para hash aqui se necessário:
            # usuario.set_password(form_usuario.cleaned_data['password'])
            
            usuario.save()

            # 2. Salva o Endereço vinculado ao Usuário recém-criado
            endereco = form_endereco.save(commit=False)
            endereco.usuario = usuario
            endereco.save()

            # 3. Salva o Pet vinculado ao Usuário
            pet = form_pet.save(commit=False)
            pet.usuario = usuario
            pet.save()

            messages.success(request, 'Cadastro completo realizado com sucesso! Faça seu login.')
            return redirect('login')
        else:
            messages.error(request, 'Por favor, corrija os erros apontados nos formulários abaixo.')
    else:
        form_usuario = UsuarioForm()
        form_endereco = EnderecoForm()
        form_pet = PetForm()

    contexto = {
        'form_usuario': form_usuario,
        'form_endereco': form_endereco,
        'form_pet': form_pet,
    }
    return render(request, 'cadastro/cadastro.html', contexto)