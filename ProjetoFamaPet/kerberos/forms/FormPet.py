from django import forms
from django.utils import timezone

from ..models.pet import Pet
from ..models.usuario import Usuario 


class NomeValidationMixin:
    """Mixin para reutilização da regra de validação de nome mínimo."""
    def clean_nome(self):
        nome = self.cleaned_data.get("nome", "").strip()
        if len(nome) < 3:
            raise forms.ValidationError(
                "O nome deve ter pelo menos 3 caracteres."
            )
        return nome


class PetForm(NomeValidationMixin, forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['usuario', 'nome', 'data_de_nascimento', 'raca', 'porte', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do pet',
                'autocomplete': 'off',
            }),
            'data_de_nascimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'raca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Raça do pet (ex: Poodle, SRD)',
            }),
            'porte': forms.Select(attrs={
                'class': 'form-select',
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observações médicas, comportamento ou alimentação...',
                'rows': 4,
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Define limite de data no HTML dinamicamente a cada requisição
        if 'data_de_nascimento' in self.fields:
            self.fields['data_de_nascimento'].widget.attrs['max'] = timezone.now().date().isoformat()

        # Controle de Permissão do Campo Tutor
        if user and user.is_staff:
            if 'usuario' in self.fields:
                # Carrega todos os cadastros de Usuario ordenados por nome
                self.fields['usuario'].queryset = Usuario.objects.all().order_by('nome')
                self.fields['usuario'].label = "Tutor / Cliente"
                self.fields['usuario'].empty_label = "Selecione um Tutor / Cliente"
                self.fields['usuario'].widget = forms.Select(attrs={'class': 'form-select', 'required': 'required'})
                
                # Exibe o Nome e E-mail do Tutor no dropdown
                self.fields['usuario'].label_from_instance = lambda obj: f"{obj.nome} ({obj.email})"
        else:
            # Segurança: Remove o campo para usuários comuns
            self.fields.pop('usuario', None)

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Se não for staff, associa ao perfil de Usuario correspondente ao e-mail do login
        if self.user and not self.user.is_staff and not instance.pk:
            usuario_perfil = Usuario.objects.filter(email=self.user.email).first()
            if usuario_perfil:
                instance.usuario = usuario_perfil

        if commit:
            instance.save()
            self.save_m2m()
        return instance