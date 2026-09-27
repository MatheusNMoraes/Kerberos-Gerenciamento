from django import forms
from django.contrib.auth.models import User
from django.db import transaction
from .models import Usuario

class CadastroForm(forms.Form):
    nome = forms.CharField(max_length=100)
    email = forms.EmailField()
    telefone = forms.CharField(max_length=20)
    senha = forms.CharField(widget=forms.PasswordInput)
    confirmar_senha = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("senha") != cleaned.get("confirmar_senha"):
            raise forms.ValidationError("As senhas não coincidem.")
        return cleaned

    def save(self):
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data["email"],
                email=self.cleaned_data["email"],
                password=self.cleaned_data["senha"],
            )
            usuario = Usuario.objects.create(
                user=user,
                nome=self.cleaned_data["nome"],
                email=self.cleaned_data["email"],
                telefone=self.cleaned_data["telefone"],
            )
        return usuario