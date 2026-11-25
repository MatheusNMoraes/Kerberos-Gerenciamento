from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator

from ..models.usuario import Usuario
from .mixins import NomeValidationMixin


class ColaboradorForm(NomeValidationMixin, forms.ModelForm):
    senha = forms.CharField(
        label="Senha",
        required=False,
        validators=[MinLengthValidator(8), MaxLengthValidator(128)],
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "minlength": "8",
            "maxlength": "128",
        }),
    )
    confirmar_senha = forms.CharField(
        label="Confirmar senha",
        required=False,
        validators=[MinLengthValidator(8), MaxLengthValidator(128)],
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "minlength": "8",
            "maxlength": "128",
        }),
    )

    class Meta:
        model = Usuario
        fields = ("nome", "email", "telefone", "is_active")
        labels = {"is_active": "Conta ativa"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["senha"].required = not self.instance.pk
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-control"
                max_length = getattr(field, "max_length", None)
                if max_length:
                    field.widget.attrs["maxlength"] = str(max_length)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.exclude(pk=self.instance.pk).filter(username=email).exists():
            raise forms.ValidationError("Este e-mail já está sendo usado como usuário.")
        return email

    def clean_senha(self):
        senha = self.cleaned_data.get("senha")
        if senha:
            try:
                validate_password(senha, self.instance)
            except ValidationError as error:
                raise forms.ValidationError(error.messages) from error
        return senha

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar_senha = cleaned_data.get("confirmar_senha")

        if senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas não coincidem.")
        if not self.instance.pk and not senha:
            self.add_error("senha", "Informe uma senha para o novo colaborador.")

        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = self.cleaned_data["email"]
        usuario.is_staff = True
        usuario.is_colaborador = True
        usuario.is_superuser = False
        if self.cleaned_data.get("senha"):
            usuario.set_password(self.cleaned_data["senha"])
        if commit:
            usuario.save()
        return usuario