from dataclasses import dataclass
from datetime import date
from typing import Any

from core.models import AnaliseLote
from src.validators import validar_lote

from .alerta import ResultadoAlerta, disparar_alerta
from .email import EmailSenderInterface
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
    alerta: ResultadoAlerta | None = None

    def para_resposta(self) -> dict[str, Any]:
        resposta = {
            "valido": self.valido,
            "dias_restantes": self.dias_restantes,
            "classificacao": (
                self.classificacao.value if self.classificacao is not None else None
            ),
            "erros": self.erros,
        }

        if self.alerta is not None:
            resposta["alerta"] = self.alerta.para_resposta()

        return resposta


def monitorar_lote(
    payload: Any,
    hoje: date,
    analise_lote: AnaliseLote | None = None,
    destinatario_alerta: str | None = None,
    email_sender: EmailSenderInterface | None = None,
) -> ResultadoMonitoramento:
    lote, erros = validar_lote(payload)

    if lote is None:
        return ResultadoMonitoramento(
            valido=False,
            dias_restantes=None,
            classificacao=None,
            erros=erros,
        )

    dias_restantes = calcular_dias_restantes(lote.data_validade, hoje)
    classificacao = classificar_risco(lote.data_validade, hoje)
    alerta = None

    if analise_lote is not None and destinatario_alerta is not None:
        alerta = disparar_alerta(
            analise_lote=analise_lote,
            classificacao=classificacao.value,
            destinatario=destinatario_alerta,
            email_sender=email_sender,
        )

    return ResultadoMonitoramento(
        valido=True,
        dias_restantes=dias_restantes,
        classificacao=classificacao,
        erros={},
        alerta=alerta,
    )
