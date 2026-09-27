from datetime import date
from django import forms
from ..models.usuario import Usuario

class NomeValidationMixin:
    def clean_nome(self):
        nome = self.cleaned_data.get("nome", "").strip()
        if len(nome) < 3:
            raise forms.ValidationError(
                "O nome deve ter pelo menos 3 caracteres."
            )
        return nome

class UsuarioForm(NomeValidationMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'telefone', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome completo',
                'autocomplete': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'seuemail@exemplo.com',
                'autocomplete': 'email',
            }),
            'telefone': forms.TextInput(attrs={
                'placeholder': '(11) 91234-5678',
                'autocomplete': 'tel',
            }),
        }
        error_messages = {
            'email': {
                'unique': "Já existe um usuário cadastrado com este e-mail.",
            },
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        query = Usuario.objects.filter(email=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError(
                "Já existe um usuário cadastrado com este e-mail."
            )
        return email

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '').strip()
        numeros = "".join(filter(str.isdigit, telefone))

        if len(numeros) not in (10, 11):
            raise forms.ValidationError(
                "Informe um telefone válido com DDD."
            )
        return numeros