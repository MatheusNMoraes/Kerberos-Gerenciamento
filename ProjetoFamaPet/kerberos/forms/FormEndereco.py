from datetime import date
from django import forms
from .. import models

class EnderecoForm(forms.ModelForm):
    class Meta:
        model = models.Endereco
        fields = ['rua', 'numero', 'bairro', 'cep']
        widgets = {
            'rua': forms.TextInput(attrs={
                'placeholder': 'Rua/Avenida',
                'autocomplete': 'street-address',
            }),
            'numero': forms.NumberInput(attrs={
                'placeholder': 'Número',
                'min': 1,
            }),
            'bairro': forms.TextInput(attrs={
                'placeholder': 'Bairro',
                'autocomplete': 'address-level2',
            }),
            'cep': forms.TextInput(attrs={
                'placeholder': '00000-000',
                'maxlength': 9,
                'autocomplete': 'postal-code',
            }),
        }

    def clean_cep(self):
        cep = "".join(filter(str.isdigit, self.cleaned_data["cep"]))

        if len(cep) != 8:
            raise forms.ValidationError("O CEP deve conter 8 dígitos.")
        return f"{cep[:5]}-{cep[5:]}"

    def clean_numero(self):
        numero = self.cleaned_data.get("numero")

        if numero is not None and numero <= 0:
            raise forms.ValidationError(
                "O número deve ser maior que zero."
            )
        return numero
