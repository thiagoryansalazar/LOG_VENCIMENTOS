from __future__ import annotations

import logging
from dataclasses import dataclass

from django.utils import timezone

from core.models import Alerta, AnaliseLote

from .email import EmailSenderInterface, carregar_email_sender, email_rate_limiter
from .vencimento import ClassificacaoRisco

logger = logging.getLogger(__name__)

CLASSIFICACOES_ALERTAVEIS = {
    ClassificacaoRisco.CRITICO.value,
    ClassificacaoRisco.VENCIDO.value,
}


@dataclass(frozen=True, slots=True)
class ResultadoAlerta:
    enviado: bool
    suprimido: bool
    motivo: str
    alerta_id: int | None = None

    def para_resposta(self) -> dict[str, object]:
        return {
            "enviado": self.enviado,
            "suprimido": self.suprimido,
            "motivo": self.motivo,
            "alerta_id": self.alerta_id,
        }


def alerta_recente_existe(
    analise_lote: AnaliseLote,
    classificacao: str,
):
    limite = timezone.now() - timezone.timedelta(hours=24)
    return (
        Alerta.objects.filter(
            analise_lote=analise_lote,
            classificacao=classificacao,
            enviado_em__gte=limite,
        )
        .order_by("-enviado_em")
        .first()
    )


def construir_assunto(analise_lote: AnaliseLote, classificacao: str) -> str:
    return f"ATLAS Vencimentos - lote {classificacao}: {analise_lote.lote}"


def construir_corpo(analise_lote: AnaliseLote, classificacao: str) -> str:
    return (
        "Alerta de vencimento do ATLAS Vencimentos.\n\n"
        f"Produto: {analise_lote.codigo_produto}\n"
        f"Lote: {analise_lote.lote}\n"
        f"Data de validade: {analise_lote.data_validade.isoformat()}\n"
        f"Dias restantes: {analise_lote.dias_restantes}\n"
        f"Classificacao: {classificacao}\n"
        f"Origem: {analise_lote.origem}\n"
    )


def disparar_alerta(
    analise_lote: AnaliseLote,
    classificacao: str,
    destinatario: str,
    email_sender: EmailSenderInterface | None = None,
    rate_limiter=email_rate_limiter,
) -> ResultadoAlerta:
    if classificacao not in CLASSIFICACOES_ALERTAVEIS:
        return ResultadoAlerta(
            enviado=False,
            suprimido=True,
            motivo="classificacao sem alerta",
        )

    alerta_existente = alerta_recente_existe(analise_lote, classificacao)
    if alerta_existente is not None:
        logger.info(
            "alerta suprimido: analise_lote=%s classificacao=%s",
            analise_lote.id,
            classificacao,
        )
        return ResultadoAlerta(
            enviado=False,
            suprimido=True,
            motivo="alerta suprimido por duplicidade em 24h",
            alerta_id=alerta_existente.id,
        )

    if not rate_limiter.permitir():
        logger.error("rate limit de email excedido")
        return ResultadoAlerta(
            enviado=False,
            suprimido=True,
            motivo="rate limit de email excedido",
        )

    sender = email_sender or carregar_email_sender()
    assunto = construir_assunto(analise_lote, classificacao)
    corpo = construir_corpo(analise_lote, classificacao)
    sender.enviar(destinatario, assunto, corpo)

    alerta = Alerta.objects.create(
        analise_lote=analise_lote,
        classificacao=classificacao,
        mensagem=corpo,
        destinatario=destinatario,
        enviado_em=timezone.now(),
    )

    return ResultadoAlerta(
        enviado=True,
        suprimido=False,
        motivo="alerta enviado",
        alerta_id=alerta.id,
    )
