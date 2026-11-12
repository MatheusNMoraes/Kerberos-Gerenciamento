from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages

from ..forms.FormUsuario import UsuarioForm
from ..forms.FormEndereco import EnderecoForm 
from ..forms.FormPet import PetForm


@transaction.atomic
def cadastrar_usuario(request):
    if request.method == 'POST':
        form_usuario = UsuarioForm(
            request.POST, prefix='usuario', exigir_aceite=True
        )
        form_endereco = EnderecoForm(request.POST, prefix='endereco')
        form_pet = PetForm(request.POST, prefix='pet')

        if form_usuario.is_valid() and form_endereco.is_valid() and form_pet.is_valid():
            endereco = form_endereco.save()
            usuario = form_usuario.save(commit=False)
            usuario.endereco = endereco
            usuario.save()

            pet = form_pet.save(commit=False)
            pet.usuario = usuario
            pet.save()

            messages.success(request, 'Cadastro completo realizado com sucesso! Faça seu login.')
            return redirect('login')
        else:
            messages.error(request, 'Por favor, corrija os erros apontados nos formulários abaixo.')
    else:
        form_usuario = UsuarioForm(prefix='usuario', exigir_aceite=True)
        form_endereco = EnderecoForm(prefix='endereco')
        form_pet = PetForm(prefix='pet')

    contexto = {
        'form_usuario': form_usuario,
        'form_endereco': form_endereco,
        'form_pet': form_pet,
    }
    return render(request, 'cadastro/cadastro.html', contexto)
