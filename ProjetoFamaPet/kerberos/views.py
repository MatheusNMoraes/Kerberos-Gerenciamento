from django.shortcuts import render, get_object_or_404
from .models import Usuario, Pet

def home(request):
    return render(request, 'home/home.html')


def listar_usuarios(request):
    usuarios = Usuario.objects.all()
    contexto = {'usuarios': usuarios}
    return render(request, 'usuario/listar_usuarios.html', contexto)