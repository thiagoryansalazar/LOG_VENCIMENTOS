from datetime import date
from enum import StrEnum


class ClassificacaoRisco(StrEnum):
    VENCIDO = "VENCIDO"
    CRITICO = "CRITICO"
    ATENCAO = "ATENCAO"
    NORMAL = "NORMAL"


def calcular_dias_restantes(
    data_validade: date,
    hoje: date | None = None,
) -> int:
    data_referencia = hoje or date.today()
    return (data_validade - data_referencia).days


def classificar_risco(
    data_validade: date,
    hoje: date | None = None,
) -> ClassificacaoRisco:
    dias_restantes = calcular_dias_restantes(data_validade, hoje)

    if dias_restantes <= 0:
        return ClassificacaoRisco.VENCIDO
    if dias_restantes <= 7:
        return ClassificacaoRisco.CRITICO
    if dias_restantes <= 30:
        return ClassificacaoRisco.ATENCAO
    return ClassificacaoRisco.NORMAL
