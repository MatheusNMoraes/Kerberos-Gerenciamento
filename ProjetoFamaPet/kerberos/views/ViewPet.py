from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from ..forms.FormPet import PetForm
from ..models.pet import Pet


def _get_pet_or_404(user, pk):
    """
    Garante que a busca do Pet respeite as permissões.
    - Staff/Admin: acessa qualquer pet.
    - Cliente comum: acessa apenas os seus próprios pets.
    """
    if user.is_staff:
        queryset = Pet.objects.all()
    else:
        queryset = Pet.objects.filter(usuario=user)

    return get_object_or_404(queryset, pk=pk)


@login_required
def listar_pets(request):
    """
    Lista os pets cadastrados com suporte a busca e paginação.
    - Administradores visualizam todos os pets e podem buscar por tutor.
    - Clientes visualizam apenas seus próprios pets.
    """
    query = request.GET.get('q', '').strip()
    
    pets_list = Pet.objects.select_related('usuario')

    # REGRA DE ACESSO: clientes veem apenas os seus próprios pets
    if not request.user.is_staff:
        pets_list = pets_list.filter(usuario=request.user)

    if query:
        filtros = Q(nome__icontains=query) | Q(raca__icontains=query)
        
        # Apenas staff pode filtrar buscando dados do Tutor (nome/e-mail)
        if request.user.is_staff:
            filtros |= Q(usuario__nome__icontains=query) | Q(usuario__email__icontains=query)
            
        pets_list = pets_list.filter(filtros)

    paginator = Paginator(pets_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'pets': page_obj,
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'pet/pets.html', contexto)


@login_required
def criar_pet(request):
    """Cadastra um novo Pet."""
    if request.user.is_colaborador:
        raise PermissionDenied

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

    return render(request, 'pet/pet_form.html', {
        'form': form,
        'titulo': 'Cadastrar Novo Pet'
    })


@login_required
def editar_pet(request, pk):
    """Edita os dados de um Pet existente."""
    if request.user.is_colaborador:
        raise PermissionDenied

    pet = _get_pet_or_404(request.user, pk)

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

    return render(request, 'pet/pet_form.html', {
        'form': form,
        'pet': pet,
        'titulo': f'Editar Pet: {pet.nome}'
    })


@login_required
@require_POST
def deletar_pet(request, pk):
    """Deleta o Pet com verificação de permissão."""
    if request.user.is_colaborador:
        raise PermissionDenied

    pet = _get_pet_or_404(request.user, pk)
    nome_pet = pet.nome
    pet.delete()
    messages.success(request, f'Pet "{nome_pet}" removido com sucesso!')
    return redirect('listar_pets')