from django.contrib.auth.forms import UserCreationForm

from ..models.usuario import Usuario


class AdminUsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'nome', 'telefone', 'is_active', 'is_staff')