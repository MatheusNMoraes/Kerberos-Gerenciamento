from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms.FormPet import PetForm
from ..models.pet import Pet


@login_required
def listar_pets(request):
    if request.user.is_staff or request.user.is_superuser:
        pets = Pet.objects.select_related('usuario').all()
    else:
        pets = Pet.objects.select_related('usuario').filter(usuario=request.user)
        
    return render(request, 'pet/pets.html', {'pets': pets})


@login_required
def criar_pet(request):
    if request.method == 'POST':
        form = PetForm(request.POST, user=request.user)
        if form.is_valid():
            pet = form.save()
            messages.success(request, f'Pet "{pet.nome}" cadastrado com sucesso!')
            return redirect('listar_pets')
        else:
            messages.error(request, 'Erro ao cadastrar o pet. Por favor, verifique os campos abaixo.')
    else:
        form = PetForm(user=request.user)

    return render(request, 'pet/criar_pet.html', {'form': form})


@login_required
def editar_pet(request, pk):
    if request.user.is_staff or request.user.is_superuser:
        pet = get_object_or_404(Pet, pk=pk)
    else:
        pet = get_object_or_404(Pet, pk=pk, usuario=request.user)

    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Pet "{pet.nome}" atualizado com sucesso!')
            return redirect('listar_pets')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = PetForm(instance=pet, user=request.user)

    return render(request, 'pet/editar_pet.html', {
        'form': form,
        'pet': pet
    })



@login_required
def deletar_pet(request, pk):
    if request.user.is_staff or request.user.is_superuser:
        pet = get_object_or_404(Pet, pk=pk)
    else:
        pet = get_object_or_404(Pet, pk=pk, usuario=request.user)

    if request.method == 'POST':
        nome_pet = pet.nome
        pet.delete()
        messages.success(request, f'Pet "{nome_pet}" removido com sucesso!')
        return redirect('listar_pets')

    return render(request, 'pet/deletar_pet.html', {'pet': pet})