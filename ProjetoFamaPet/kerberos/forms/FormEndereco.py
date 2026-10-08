from django import forms
from ..models.endereco import Endereco


class EnderecoForm(forms.ModelForm):
    class Meta:
        model = Endereco
        fields = ['cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf']
        widgets = {
            'cep': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': '00000-000',
                'id': 'id_cep',
                'maxlength': '9',
                'autocomplete': 'postal-code',
            }),
            'logradouro': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Rua / Avenida',
                'id': 'id_logradouro',
                'autocomplete': 'address-line1',
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Ex: 123 ou S/N',
                'id': 'id_numero',
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Apto, Bloco, Casa 2 (Opcional)',
                'id': 'id_complemento',
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Bairro',
                'id': 'id_bairro',
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control custom-input',
                'placeholder': 'Cidade',
                'id': 'id_cidade',
            }),
            'uf': forms.Select(attrs={
                'class': 'form-select custom-input',
                'id': 'id_uf',
            }),
        }

    def clean_cep(self):
        cep = "".join(filter(str.isdigit, self.cleaned_data.get("cep", "")))
        if len(cep) != 8:
            raise forms.ValidationError("O CEP deve conter exatamente 8 dígitos.")
        return f"{cep[:5]}-{cep[5:]}"