from datetime import date
from django import forms
from ..models import Pet

class NomeValidationMixin:
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
        fields = ['nome', 'data_de_nascimento', 'raca', 'porte', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome do pet',
                'autocomplete': 'name',
            }),

            'data_de_nascimento': forms.DateInput(attrs={
                'type': 'date',
                'max': date.today().isoformat(),
            }),

            'raca': forms.TextInput(attrs={
                'placeholder': 'Raça do pet',
            }),

            'porte': forms.Select(),

            'observacao': forms.Textarea(attrs={
                'placeholder': 'Observações sobre o pet',
                'rows': 4,
            }),
        }
    
    def clean_data_de_nascimento(self):
        data_de_nascimento = self.cleaned_data.get("data_de_nascimento")
        if data_de_nascimento and data_de_nascimento > date.today():
            raise forms.ValidationError(
                "A data de nascimento não pode ser no futuro."
            )
        return data_de_nascimento 