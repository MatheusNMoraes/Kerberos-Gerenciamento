from django import forms
from django.core.validators import MaxValueValidator
from kerberos.models.servico import Servico


class ServicoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["descricao"].widget.attrs["maxlength"] = "500"
        self.fields["duracao_minutos"].validators.append(
            MaxValueValidator(1440, message="A duração máxima é de 1440 minutos.")
        )

    def clean_descricao(self):
        descricao = self.cleaned_data.get("descricao", "").strip()
        if len(descricao) > 500:
            raise forms.ValidationError("A descrição pode ter no máximo 500 caracteres.")
        return descricao

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