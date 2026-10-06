from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..forms.FormPet import PetForm
from ..models import Pet

@login_required
def listar_pets(request):
    if request.user.is_staff or request.user.is_superuser:
        pets = Pet.objects.all()
    else:
        pets = Pet.objects.filter(usuario=request.user)
        
    return render(request, 'pet/pets.html', {'pets': pets})

@login_required
def criar_pet(request):
    if request.method == 'POST':
        form = FormPet(request.POST)
        if form.is_valid():
            pet = form.save(commit=False)

            if not (request.user.is_staff or request.user.is_superuser):
                pet.usuario = request.user
            pet.save()
            messages.success(request, 'Pet cadastrado com sucesso!')
            return redirect('pets')
    else:
        form = PetForm()
    return render(request, 'pet/form_pet.html', {'form': form})

@login_required
def editar_pet(request, pk):
    if request.user.is_staff or request.user.is_superuser:
        pet = get_object_or_404(Pet, pk=pk)
    else:
        pet = get_object_or_404(Pet, pk=pk, usuario=request.user)

    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pet atualizado com sucesso!')
            return redirect('pets')
    else:
        form = PetForm(instance=pet)
    return render(request, 'pet/pet_form.html', {'form': form})

@login_required
def deletar_pet(request, pk):
    if request.user.is_staff or request.user.is_superuser:
        pet = get_object_or_404(Pet, pk=pk)
    else:
        pet = get_object_or_404(Pet, pk=pk, usuario=request.user)

    if request.method == 'POST':
        pet.delete()
        messages.success(request, 'Pet removido com sucesso!')
        return redirect('pets')
    return render(request, 'pet/pet_deletar.html', {'pet': pet})