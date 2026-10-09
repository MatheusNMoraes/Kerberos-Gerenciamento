from decimal import Decimal
from datetime import timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Agendamento(models.Model):

    class StatusChoices(models.TextChoices):
        PENDENTE = "Pendente", "Pendente"
        CONFIRMADO = "Confirmado", "Confirmado"
        CONCLUIDO = "Concluido", "Concluido"
        CANCELADO = "Cancelado", "Cancelado"

    usuario = models.ForeignKey(
        "Usuario",
        on_delete=models.CASCADE,
        related_name="agendamentos"
    )

    pet = models.ForeignKey(
        "Pet",
        on_delete=models.CASCADE,
        related_name="agendamentos"
    )

    data = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDENTE
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["-data"]

    @property
    def valor_total(self):
        """Soma o valor congelado de todos os itens do agendamento."""
        return sum(
            (item.preco_unitario for item in self.itens.all()),
            Decimal("0.00")
        )

    @property
    def duracao_total_minutos(self):
        """Soma a duração total estimada de todos os serviços agendados."""
        return sum(item.duracao_minutos for item in self.itens.all())

    @property
    def data_fim_estimada(self):
        """Calcula a hora prevista de término do atendimento."""
        if self.data:
            return self.data + timedelta(minutes=self.duracao_total_minutos)
        return None

    @property
    def lista_servicos(self):
        """Retorna os nomes dos serviços separados por vírgula."""
        return ", ".join(item.servico_nome for item in self.itens.all())

    def __str__(self):
        data_fmt = self.data.strftime('%d/%m/%Y %H:%M') if self.data else 'Sem data'
        pet_nome = self.pet.nome if self.pet_id else 'Sem Pet'
        return f"{pet_nome} - {data_fmt} ({self.status})"


class ItemAgendamento(models.Model):
    """
    Tabela intermediária que congela o valor do serviço e a duração 
    no momento exato em que o agendamento foi realizado.
    """
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name="itens"
    )
    servico = models.ForeignKey(
        "Servico",
        on_delete=models.PROTECT,
        related_name="itens_agendados"
    )
    servico_nome = models.CharField(max_length=100)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Item do Agendamento"
        verbose_name_plural = "Itens do Agendamento"

    def __str__(self):
        return f"{self.servico_nome} - R$ {self.preco_unitario} ({self.duracao_minutos} min)"