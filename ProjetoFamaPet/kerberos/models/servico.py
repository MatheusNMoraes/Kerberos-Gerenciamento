from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator


class Servico(models.Model):

    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome do Serviço",
        help_text="Ex: Banho e Tosa, Corte de Unha, Tosa Higiênica"
    )

    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição",
        help_text="Descrição detalhada do que está incluso no serviço"
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01"), 
                message="O valor deve ser de no mínimo R$ 0,01."
            )
        ],
        verbose_name="Preço (R$)"
    )

    duracao_minutos = models.PositiveIntegerField(
        default=30,
        validators=[
            MinValueValidator(5, message="A duração mínima é de 5 minutos.")
        ],
        verbose_name="Duração estimada (minutos)",
        help_text="Tempo médio necessário para realizar o serviço"
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Desmarque para desativar o serviço sem apagar o histórico"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["ativo", "nome"]),
        ]

    def __str__(self):
        return f"{self.nome} - R$ {self.valor}"

    def clean(self):
        super().clean()
        if self.nome:
            self.nome = self.nome.strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)