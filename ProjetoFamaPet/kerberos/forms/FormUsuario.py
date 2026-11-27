from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from ..models import Usuario
from .mixins import NomeValidationMixin


class UsuarioForm(NomeValidationMixin, forms.ModelForm):

    aceita_regulamento = forms.BooleanField(
        label="Li e concordo com o regulamento.",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    senha = forms.CharField(
        label="Senha",
        validators=[MinLengthValidator(8), MaxLengthValidator(128)],
        widget=forms.PasswordInput(attrs={
            "placeholder": "Crie uma senha segura",
            "autocomplete": "new-password",
            "class": "form-control",
            "minlength": "8",
            "maxlength": "128",
        }),
    )
    confirmar_senha = forms.CharField(
        label="Confirme a Senha",
        validators=[MinLengthValidator(8), MaxLengthValidator(128)],
        widget=forms.PasswordInput(attrs={
            "placeholder": "Repita a senha",
            "autocomplete": "new-password",
            "class": "form-control",
            "minlength": "8",
            "maxlength": "128",
        }),
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'telefone']
        error_messages = {
            'email': {
                'unique': "Já existe um usuário cadastrado com este e-mail.",
            },
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Nome completo',
                'autocomplete': 'name',
                'class': 'form-control',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'seuemail@exemplo.com',
                'autocomplete': 'email',
                'class': 'form-control',
            }),
            'telefone': forms.TextInput(attrs={
                'placeholder': '(11) 91234-5678',
                'autocomplete': 'tel',
                'inputmode': 'tel',
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        exigir_aceite = kwargs.pop("exigir_aceite", False)
        super().__init__(*args, **kwargs)
        self.fields['aceita_regulamento'].required = exigir_aceite
        if self.instance.pk:
            self.fields['senha'].required = False
            self.fields['confirmar_senha'].required = False

        for nome_campo, campo in self.fields.items():
            classes = campo.widget.attrs.get('class', '').split()
            max_length = getattr(campo, 'max_length', None)
            if max_length:
                campo.widget.attrs['maxlength'] = str(max_length)
            if nome_campo == 'telefone':
                campo.widget.attrs.update({
                    'inputmode': 'tel',
                    'pattern': r'\(?[0-9]{2}\)?[\s-]?[0-9]{4,5}-?[0-9]{4}',
                })
            if nome_campo in self.errors:
                classes.append('is-invalid')
                campo.widget.attrs['aria-invalid'] = 'true'
                campo.widget.attrs['aria-describedby'] = f'id_{nome_campo}-error'
            else:
                campo.widget.attrs['aria-invalid'] = 'false'
            campo.widget.attrs['class'] = ' '.join(dict.fromkeys(classes))

    def clean_senha(self):
        senha = self.cleaned_data.get('senha')
        if senha:
            try:
                validate_password(senha, self.instance)
            except DjangoValidationError as error:
                raise forms.ValidationError(error.messages) from error
        return senha

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if email:
            return email.strip().lower()
        return email

    def clean_telefone(self):
        telefone = (self.cleaned_data.get('telefone') or '').strip()
        if not telefone:
            return ''

        numeros = "".join(filter(str.isdigit, telefone))

        if len(numeros) not in (10, 11):
            raise forms.ValidationError(
                "Informe um telefone válido com DDD (10 ou 11 dígitos)."
            )

        if len(numeros) == 11:
            return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
        elif len(numeros) == 10:
            return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"

        return telefone

    def clean(self):
        """Valida se as duas senhas informadas batem."""
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if (senha or confirmar_senha) and senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas não coincidem.")

        return cleaned_data

    def save(self, commit=True):
        """Preenche o username com o e-mail, aplica a criptografia e salva."""
        usuario = super().save(commit=False)
        
        email_limpo = self.cleaned_data.get("email")
        usuario.username = email_limpo
        
        senha = self.cleaned_data.get('senha')
        if senha:
            usuario.set_password(senha)
        elif not usuario.pk:
            usuario.set_unusable_password()
        
        if commit:
            usuario.save()
        return usuario