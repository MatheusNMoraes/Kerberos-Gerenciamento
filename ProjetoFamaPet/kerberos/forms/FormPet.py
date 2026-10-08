from datetime import date
from django import forms
from django.contrib.auth.models import User
from ..models.pet import Pet


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
        fields = ['usuario', 'nome', 'data_de_nascimento', 'raca', 'porte', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do pet',
                'autocomplete': 'name',
            }),
            'data_de_nascimento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().isoformat(),
            }),
            'raca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Raça do pet',
            }),
            'porte': forms.Select(attrs={
                'class': 'form-select',
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observações sobre o pet',
                'rows': 4,
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if 'usuario' in self.fields:
            if user and user.is_staff:
                self.fields['usuario'].queryset = User.objects.all().order_by('first_name', 'username')
                self.fields['usuario'].label = "Tutor / Cliente"
                self.fields['usuario'].empty_label = "Selecione um Tutor / Cliente"
                self.fields['usuario'].widget = forms.Select(attrs={'class': 'form-select', 'required': 'required'})
                self.fields['usuario'].label_from_instance = lambda obj: (
                    f"{obj.get_full_name()} ({obj.username})" if obj.get_full_name() else obj.username
                )
            else:
                self.fields['usuario'].required = False
                self.fields['usuario'].widget = forms.HiddenInput()

    def clean_data_de_nascimento(self):
        data_de_nascimento = self.cleaned_data.get("data_de_nascimento")
        if data_de_nascimento and data_de_nascimento > date.today():
            raise forms.ValidationError(
                "A data de nascimento não pode ser no futuro."
            )
        return data_de_nascimento

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Se for cliente comum (não staff) criando pet, vincula automaticamente ao seu próprio usuário
        if self.user and not self.user.is_staff and not instance.usuario_id:
            instance.usuario = self.user
        
        if commit:
            instance.save()
            self.save_m2m()
        return instance