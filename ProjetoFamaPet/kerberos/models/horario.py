from django.core.exceptions import ValidationError
from django.db import models


DIAS_DA_SEMANA = (
    (0, "Segunda-feira"),
    (1, "Terça-feira"),
    (2, "Quarta-feira"),
    (3, "Quinta-feira"),
    (4, "Sexta-feira"),
    (5, "Sábado"),
    (6, "Domingo"),
)


class FaixaHorarioMixin:
    def validar_faixa(self, campos_obrigatorios):
        inicio = self.hora_abertura
        fim = self.hora_fechamento
        pausa_inicio = self.pausa_inicio
        pausa_fim = self.pausa_fim

        if self.fechado:
            return

        if campos_obrigatorios and (not inicio or not fim):
            raise ValidationError("Informe os horários de abertura e fechamento.")
        if not inicio or not fim:
            return
        if inicio >= fim:
            raise ValidationError({"hora_fechamento": "O fechamento deve ser após a abertura."})
        if bool(pausa_inicio) != bool(pausa_fim):
            raise ValidationError("Informe o início e o fim da pausa.")
        if pausa_inicio and not (inicio < pausa_inicio < pausa_fim < fim):
            raise ValidationError("A pausa deve ficar dentro do horário de funcionamento.")


class HorarioFuncionamento(FaixaHorarioMixin, models.Model):
    dia_semana = models.PositiveSmallIntegerField(
        choices=DIAS_DA_SEMANA,
        unique=True,
    )
    fechado = models.BooleanField(default=True)
    hora_abertura = models.TimeField(null=True, blank=True)
    hora_fechamento = models.TimeField(null=True, blank=True)
    pausa_inicio = models.TimeField(null=True, blank=True)
    pausa_fim = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ["dia_semana"]
        verbose_name = "Horário semanal"
        verbose_name_plural = "Horários semanais"

    def clean(self):
        super().clean()
        self.validar_faixa(campos_obrigatorios=not self.fechado)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_dia_semana_display()


class ExcecaoHorario(FaixaHorarioMixin, models.Model):
    data = models.DateField(unique=True)
    fechado = models.BooleanField(default=True)
    hora_abertura = models.TimeField(null=True, blank=True)
    hora_fechamento = models.TimeField(null=True, blank=True)
    pausa_inicio = models.TimeField(null=True, blank=True)
    pausa_fim = models.TimeField(null=True, blank=True)
    motivo = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["data"]
        verbose_name = "Exceção de horário"
        verbose_name_plural = "Exceções de horário"

    def clean(self):
        super().clean()
        self.validar_faixa(campos_obrigatorios=not self.fechado)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.data:%d/%m/%Y} - {'Fechado' if self.fechado else 'Horário especial'}"