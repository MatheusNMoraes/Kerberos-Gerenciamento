from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from kerberos.forms.FormColaborador import ColaboradorForm
from kerberos.models.usuario import Usuario


@login_required
def listar_colaboradores(request):
    colaboradores = Usuario.objects.filter(is_colaborador=True).order_by("nome")
    return render(
        request,
        "colaborador/colaboradores.html",
        {"colaboradores": colaboradores},
    )


@login_required
def criar_colaborador(request):
    form = ColaboradorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        colaborador = form.save()
        messages.success(request, f"Colaborador {colaborador.nome} cadastrado.")
        return redirect("listar_colaboradores")

    return render(
        request,
        "colaborador/colaborador_form.html",
        {"form": form, "titulo": "Novo colaborador"},
    )


@login_required
def editar_colaborador(request, pk):
    colaborador = get_object_or_404(Usuario, pk=pk, is_colaborador=True)
    form = ColaboradorForm(
        request.POST or None,
        instance=colaborador,
    )
    if request.method == "POST" and form.is_valid():
        colaborador = form.save()
        messages.success(request, f"Dados de {colaborador.nome} atualizados.")
        return redirect("listar_colaboradores")

    return render(
        request,
        "colaborador/colaborador_form.html",
        {
            "form": form,
            "colaborador": colaborador,
            "titulo": "Editar colaborador",
        },
    )


@login_required
@require_POST
def alternar_status_colaborador(request, pk):
    colaborador = get_object_or_404(Usuario, pk=pk, is_colaborador=True)
    if colaborador == request.user:
        messages.error(request, "Não é possível desativar a própria conta.")
    else:
        colaborador.is_active = not colaborador.is_active
        colaborador.save(update_fields=["is_active"])
        estado = "ativado" if colaborador.is_active else "desativado"
        messages.success(request, f"Colaborador {colaborador.nome} {estado}.")
    return redirect("listar_colaboradores")