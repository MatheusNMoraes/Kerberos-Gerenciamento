from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Pet(models.Model):

    class Porte(models.TextChoices):
        PEQUENO = "Pequeno", "Pequeno"
        MEDIO = "Médio", "Médio"
        GRANDE = "Grande", "Grande"

    nome = models.CharField(
        max_length=100, 
        db_index=True, 
        verbose_name="Nome do Pet"
    )
    data_de_nascimento = models.DateField(
        verbose_name="Data de nascimento do pet"
    )
    raca = models.CharField(
        max_length=50, 
        verbose_name="Raça"
    )
    porte = models.CharField(
        max_length=20, 
        choices=Porte.choices, 
        verbose_name="Porte"
    )
    observacao = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Observação"
    )
    # APONTAMENTO CORRETO: Referência relativa ao modelo Usuario dentro da mesma app
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        related_name='pets',
        verbose_name="Tutor"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pet"
        verbose_name_plural = "Pets"
        ordering = ['-criado_em']

    def __str__(self):
        nome_tutor = getattr(self.usuario, 'nome', str(self.usuario))
        return f"{self.nome} (Tutor: {nome_tutor})"

    def clean(self):
        super().clean()

        if self.nome:
            self.nome = self.nome.strip()
        if self.raca:
            self.raca = self.raca.strip()
        if self.observacao:
            self.observacao = self.observacao.strip()

        if self.data_de_nascimento and self.data_de_nascimento > timezone.now().date():
            raise ValidationError({
                "data_de_nascimento": "A data de nascimento não pode ser maior que a data atual."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def idade(self):
        """Calcula a idade em anos de forma dinâmica."""
        if not self.data_de_nascimento:
            return None
        hoje = timezone.now().date()
        return hoje.year - self.data_de_nascimento.year - (
            (hoje.month, hoje.day) < (self.data_de_nascimento.month, self.data_de_nascimento.day)
        )