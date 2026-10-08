from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


class Usuario(models.Model):
    telefone_validator = RegexValidator(
        regex=r'^\(?\d{2}\)?[\s-]?\d{4,5}-?\d{4}$',
        message="Informe um telefone válido. Ex: (11) 91234-5678 ou 11912345678."
    )

    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    telefone = models.CharField(max_length=20, validators=[telefone_validator])
    
    endereco = models.ForeignKey(
        "Endereco",
        on_delete=models.SET_NULL,
        related_name="usuarios",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()

        nome_validacao = self.nome.strip() if self.nome else ""
        if len(nome_validacao) < 3:
            raise ValidationError(
                {"nome": "O nome deve ter pelo menos 3 caracteres."}
            )

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.strip()
        if self.email:
            self.email = self.email.strip().lower()
        if self.telefone:
            self.telefone = self.telefone.strip()

        self.full_clean()
        super().save(*args, **kwargs)