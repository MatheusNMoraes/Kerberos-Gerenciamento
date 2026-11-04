from datetime import datetime, timedelta

from django.utils import timezone

from kerberos.models.agendamento import Agendamento
from kerberos.models.horario import ExcecaoHorario, HorarioFuncionamento


INTERVALO_SLOT_MINUTOS = 30


def _faixas_do_dia(data):
    excecao = ExcecaoHorario.objects.filter(data=data).first()
    if excecao:
        if excecao.fechado:
            return []
        horario = excecao
    else:
        horario = HorarioFuncionamento.objects.filter(
            dia_semana=data.weekday(),
            fechado=False,
        ).first()

    if not horario:
        return []

    faixas = [(horario.hora_abertura, horario.hora_fechamento)]
    if horario.pausa_inicio and horario.pausa_fim:
        faixas = [
            (horario.hora_abertura, horario.pausa_inicio),
            (horario.pausa_fim, horario.hora_fechamento),
        ]
    return faixas


def bloquear_configuracao_dia(data):
    excecao = ExcecaoHorario.objects.select_for_update().filter(data=data).first()
    if excecao is None:
        HorarioFuncionamento.objects.select_for_update().filter(
            dia_semana=data.weekday(),
        ).first()


def horarios_disponiveis(data, duracao_minutos, agendamento_id=None):
    if not duracao_minutos or duracao_minutos < 1:
        return []

    faixas = _faixas_do_dia(data)
    if not faixas:
        return []

    agendamentos = Agendamento.objects.filter(
        data__date=data,
        status__in=(
            Agendamento.StatusChoices.PENDENTE,
            Agendamento.StatusChoices.CONFIRMADO,
        ),
    ).prefetch_related("itens")
    if agendamento_id:
        agendamentos = agendamentos.exclude(pk=agendamento_id)
    ocupados = [
        (agendamento.data, agendamento.data_fim_estimada)
        for agendamento in agendamentos
    ]

    agora = timezone.localtime()
    fuso = timezone.get_current_timezone()
    duracao = timedelta(minutes=duracao_minutos)
    passo = timedelta(minutes=INTERVALO_SLOT_MINUTOS)
    horarios = []

    for hora_inicio, hora_fim in faixas:
        inicio = timezone.make_aware(datetime.combine(data, hora_inicio), fuso)
        fim = timezone.make_aware(datetime.combine(data, hora_fim), fuso)
        candidato = inicio

        while candidato + duracao <= fim:
            termino = candidato + duracao
            conflita = any(
                candidato < ocupado_fim and termino > ocupado_inicio
                for ocupado_inicio, ocupado_fim in ocupados
            )
            if candidato > agora and not conflita:
                horarios.append(candidato)
            candidato += passo

    return horarios