from datetime import date
from enum import StrEnum

from django.conf import settings


class ClassificacaoRisco(StrEnum):
    VENCIDO = "VENCIDO"
    CRITICO = "CRITICO"
    ATENCAO = "ATENCAO"
    NORMAL = "NORMAL"


def calcular_dias_restantes(
    data_validade: date,
    hoje: date,
) -> int:
    return (data_validade - hoje).days


def classificar_risco(
    data_validade: date,
    hoje: date,
) -> ClassificacaoRisco:
    dias_restantes = calcular_dias_restantes(data_validade, hoje)

    if dias_restantes <= 0:
        return ClassificacaoRisco.VENCIDO
    if dias_restantes <= settings.DIAS_CRITICO:
        return ClassificacaoRisco.CRITICO
    if dias_restantes <= settings.DIAS_ATENCAO:
        return ClassificacaoRisco.ATENCAO
    return ClassificacaoRisco.NORMAL
