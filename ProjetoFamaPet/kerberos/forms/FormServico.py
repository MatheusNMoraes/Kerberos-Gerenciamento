from django import forms
from kerberos.models.servico import Servico


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ["nome", "descricao", "valor", "duracao_minutos", "ativo"]
        widgets = {
            "nome": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex: Banho e Tosa Completa"
            }),
            "descricao": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Descreva o que está incluso neste serviço..."
            }),
            "valor": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0.00"
            }),
            "duracao_minutos": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "5",
                "min": "5",
                "placeholder": "30"
            }),
            "ativo": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }
        labels = {
            "nome": "Nome do Serviço",
            "descricao": "Descrição",
            "valor": "Preço (R$)",
            "duracao_minutos": "Duração estimada (minutos)",
            "ativo": "Disponível para agendamento (Ativo)"
        }