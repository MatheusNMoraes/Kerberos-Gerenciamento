# models/usuario.py
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import User


class Usuario(models.Model):
    telefone_validator = RegexValidator(
        regex=r'^\(?\d{2}\)?[\s-]?\d{4,5}-?\d{4}$',
        message="Informe um telefone válido. Ex: (11) 91234-5678 ou 11912345678."
    )

    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, validators=[telefone_validator])  # was 15
    endereco = models.ForeignKey(
        "Endereco",
        on_delete=models.CASCADE,
        related_name="usuarios",
        null=True,
        blank=True
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="usuario",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()

        if self.nome:
            self.nome = self.nome.strip()
            if len(self.nome) < 3:
                raise ValidationError(
                    {"nome": "O nome deve ter pelo menos 3 caracteres."}
                )

        if self.email:
            self.email = self.email.strip().lower()

        if self.telefone:
            self.telefone = self.telefone.strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)