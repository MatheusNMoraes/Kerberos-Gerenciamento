from datetime import date
from django import forms
from .. import models

class NomeValidationMixin:
    def clean_nome(self):
        nome = self.cleaned_data.get("nome", "").strip()
        if len(nome) < 3:
            raise forms.ValidationError(
                "O nome deve ter pelo menos 3 caracteres."
            )
        return nome

class ServicoForm(NomeValidationMixin, forms.ModelForm):
    class Meta:
        model = models.Servico
        fields = ['nome', 'descricao', 'valor']
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome do Serviço',
            }),
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Descrição do Produto',
                'rows': 3,
            }),
            'valor': forms.NumberInput(attrs={
                'placeholder': 'Valor do Serviço',
                'step': '0.01',
                'min': '0',
            }),
        }
    
    def clean_valor(self):
        valor = self.cleaned_data.get("valor")

        if valor is None or valor <= 0:
            raise forms.ValidationError(
                "O valor deve ser maior que zero."
            )
        return valor