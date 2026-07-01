from dataclasses import dataclass
from datetime import date
from typing import Any

from src.validators import validar_lote

from .vencimento import (
    ClassificacaoRisco,
    calcular_dias_restantes,
    classificar_risco,
)


@dataclass(frozen=True, slots=True)
class ResultadoMonitoramento:
    valido: bool
    dias_restantes: int | None
    classificacao: ClassificacaoRisco | None
    erros: dict[str, list[str]]

    def para_resposta(self) -> dict[str, Any]:
        return {
            "valido": self.valido,
            "dias_restantes": self.dias_restantes,
            "classificacao": (
                self.classificacao.value if self.classificacao is not None else None
            ),
            "erros": self.erros,
        }


def monitorar_lote(
    payload: Any,
    hoje: date | None = None,
) -> ResultadoMonitoramento:
    lote, erros = validar_lote(payload)

    if lote is None:
        return ResultadoMonitoramento(
            valido=False,
            dias_restantes=None,
            classificacao=None,
            erros=erros,
        )

    return ResultadoMonitoramento(
        valido=True,
        dias_restantes=calcular_dias_restantes(lote.data_validade, hoje),
        classificacao=classificar_risco(lote.data_validade, hoje),
        erros={},
    )
