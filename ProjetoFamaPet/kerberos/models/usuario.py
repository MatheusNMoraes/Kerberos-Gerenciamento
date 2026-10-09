from django.contrib.auth.models import (AbstractBaseUser,BaseUserManager,PermissionsMixin,)
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, nome, password=None, **extra_fields):
        if not username:
            raise ValueError("O nome de usuário é obrigatório.")
        if not email:
            raise ValueError("O e-mail é obrigatório.")

        email = self.normalize_email(email)
        user = self.model(
            username=username.strip(),
            email=email,
            nome=nome.strip(),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, nome, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")

        return self.create_user(username, email, nome, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    telefone_validator = RegexValidator(
        regex=r"^\(?\d{2}\)?[\s-]?\d{4,5}-?\d{4}$",
        message="Informe um telefone válido. Ex: (11) 91234-5678 ou 11912345678.",
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        verbose_name="Nome de Usuário",
    )
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    email = models.EmailField(unique=True, db_index=True)
    telefone = models.CharField(
        max_length=20, validators=[telefone_validator], blank=True, null=True
    )

    endereco = models.ForeignKey(
        "Endereco",
        on_delete=models.SET_NULL,
        related_name="usuarios",
        null=True,
        blank=True,
    )

    # Controle de Acesso nativo do Django
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "nome"]

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} (@{self.username})"

    def clean(self):
        super().clean()

        nome_validacao = self.nome.strip() if self.nome else ""
        if len(nome_validacao) < 3:
            raise ValidationError(
                {"nome": "O nome deve ter pelo menos 3 caracteres."}
            )

        if self.username:
            self.username = self.username.strip()

    def save(self, *args, **kwargs):
        if self.nome:
            self.nome = self.nome.strip()
        if self.username:
            self.username = self.username.strip()
        if self.email:
            self.email = self.email.strip().lower()
        if self.telefone:
            self.telefone = self.telefone.strip()

        self.full_clean()
        super().save(*args, **kwargs)