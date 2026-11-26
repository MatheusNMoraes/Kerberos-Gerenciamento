from django import forms
from django.utils import timezone

from ..models.pet import Pet
from ..models.usuario import Usuario 
from .mixins import NomeValidationMixin


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

        limites_texto = {
            "nome": 100,
            "raca": 50,
            "observacao": 500,
        }
        for nome_campo, limite in limites_texto.items():
            campo = self.fields.get(nome_campo)
            if campo:
                campo.widget.attrs["maxlength"] = str(limite)

        if 'data_de_nascimento' in self.fields:
            hoje = timezone.now().date()
            self.fields['data_de_nascimento'].widget.attrs['max'] = hoje.isoformat()
            ano_minimo = hoje.year - Pet.IDADE_MAXIMA_ANOS
            try:
                data_minima = hoje.replace(year=ano_minimo)
            except ValueError:
                data_minima = hoje.replace(year=ano_minimo, day=28)
            self.fields['data_de_nascimento'].widget.attrs['min'] = data_minima.isoformat()

        if user and user.is_staff:
            if 'usuario' in self.fields:
                self.fields['usuario'].queryset = Usuario.objects.all().order_by('nome')
                self.fields['usuario'].label = "Tutor / Cliente"
                self.fields['usuario'].empty_label = "Selecione um Tutor / Cliente"
                self.fields['usuario'].widget = forms.Select(attrs={'class': 'form-select', 'required': 'required'})
                
                self.fields['usuario'].label_from_instance = lambda obj: f"{obj.nome} ({obj.email})"
        else:
            self.fields.pop('usuario', None)

    def clean_raca(self):
        raca = self.cleaned_data.get("raca", "").strip()
        if len(raca) < 2:
            raise forms.ValidationError("Informe uma raça com pelo menos 2 caracteres.")
        return raca

    def clean_observacao(self):
        observacao = self.cleaned_data.get("observacao", "").strip()
        if len(observacao) > 500:
            raise forms.ValidationError("As observações podem ter no máximo 500 caracteres.")
        return observacao

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user and not self.user.is_staff and not instance.pk:
            instance.usuario = self.user

        if commit:
            instance.save()
            self.save_m2m()
        return instance