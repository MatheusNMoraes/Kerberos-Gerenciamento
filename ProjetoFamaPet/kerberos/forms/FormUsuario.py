from django import forms
from ..models.usuario import Usuario


class NomeValidationMixin:
    def clean_nome(self):
        nome = self.cleaned_data.get("nome", "").strip()
        if len(nome) < 3:
            raise forms.ValidationError(
                "O nome deve ter pelo menos 3 caracteres."
            )
        return nome


class UsuarioForm(NomeValidationMixin, forms.ModelForm):

    senha = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Crie uma senha segura",
            "autocomplete": "new-password",
            "class": "form-control",
        }),
        min_length=6,
        error_messages={"min_length": "A senha deve ter no mínimo 6 caracteres."}
    )
    confirmar_senha = forms.CharField(
        label="Confirme a Senha",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Repita a senha",
            "autocomplete": "new-password",
            "class": "form-control",
        }),
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'telefone']
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
                'class': 'form-control',
            }),
        }
        error_messages = {
            'email': {
                'unique': "Já existe um usuário cadastrado com este e-mail.",
            },
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if email:
            return email.strip().lower()
        return email

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone', '').strip()
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

        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error("confirmar_senha", "As senhas não coincidem.")

        return cleaned_data

    def save(self, commit=True):
        """Preenche o username com o e-mail, aplica a criptografia e salva."""
        usuario = super().save(commit=False)
        
        # Define o e-mail limpo como o username obrigatório
        email_limpo = self.cleaned_data.get("email")
        usuario.username = email_limpo
        
        # Aplica a hash de senha nativa do Django
        usuario.set_password(self.cleaned_data["senha"])
        usuario.is_staff = False  # Garante perfil de Cliente por padrão
        
        if commit:
            usuario.save()
        return usuario