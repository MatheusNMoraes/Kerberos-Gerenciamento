from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta

ANTECEDENCIA_MINIMA = timedelta(minutes=30)


class SolicitacaoTransporte(models.Model):
    class StatusChoices(models.TextChoices):
        SOLICITADO = "solicitado", "Solicitado"
        CONFIRMADO = "confirmado", "Confirmado"
        CANCELADO = "cancelado", "Cancelado"
        CONCLUIDO = "concluido", "Concluído"

    agendamento = models.OneToOneField(
        "Agendamento",
        on_delete=models.CASCADE,
        related_name="solicitacao_transporte",
    )
    endereco_retirada = models.CharField(max_length=500)
    horario_preferido = models.DateTimeField()
    horario_confirmado = models.DateTimeField(blank=True, null=True)
    taxa = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    observacoes = models.TextField(blank=True)
    politica_aceita = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.SOLICITADO,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitação de transporte"
        verbose_name_plural = "Solicitações de transporte"
        ordering = ["-criado_em"]

    def clean(self):
        super().clean()
        errors = {}

        if not self.politica_aceita:
            errors["politica_aceita"] = (
                "É necessário aceitar a política de transporte."
            )

        if self.agendamento_id:
            data_agendamento = self.agendamento.data
            dia_agendamento = timezone.localtime(data_agendamento).date()
            limite = data_agendamento - ANTECEDENCIA_MINIMA

            if self.horario_preferido:
                dia_preferido = timezone.localtime(self.horario_preferido).date()
                if dia_preferido != dia_agendamento:
                    errors["horario_preferido"] = (
                        "A retirada precisa ser no mesmo dia do agendamento."
                    )
                elif self.horario_preferido >= limite:
                    errors["horario_preferido"] = (
                        "A retirada precisa ocorrer no minimo 30 minutos antes do agendamento."
                    )

            if self.horario_confirmado:
                dia_confirmado = timezone.localtime(self.horario_confirmado).date()
                if dia_confirmado != dia_agendamento:
                    errors["horario_confirmado"] = (
                        "A retirada confirmada precisa ser no mesmo dia do agendamento."
                    )
                elif self.horario_confirmado >= limite:
                    errors["horario_confirmado"] = (
                        "A retirada confirmada precisa ocorrer no minimo 30 minutos antes do agendamento."
                    )

        if self.status in (
            self.StatusChoices.CONFIRMADO,
            self.StatusChoices.CONCLUIDO,
        ):
            if self.horario_confirmado is None:
                errors["horario_confirmado"] = (
                    "Informe o horário de retirada confirmado."
                )
            elif (
                self.status == self.StatusChoices.CONFIRMADO
                and self.horario_confirmado <= timezone.now()
            ):
                errors["horario_confirmado"] = (
                    "O horário confirmado precisa ser futuro."
                )
            if self.taxa is None:
                errors["taxa"] = "Informe a taxa do transporte."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transporte do agendamento #{self.agendamento_id} ({self.get_status_display()})"
