from __future__ import annotations

import os
import sys
from io import StringIO
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.core.management import call_command

from core.models import Alerta, AnaliseLote, ConfiguracaoAlerta
import core.management.commands.executar_monitoramento as comando_monitoramento
from src.services.alerta import disparar_alerta as disparar_alerta_real
from src.services.email import EmailSenderInterface


class FakeSender(EmailSenderInterface):
    envios: list[dict[str, str]] = []

    def enviar(self, destinatario: str, assunto: str, corpo: str) -> None:
        self.envios.append(
            {
                "destinatario": destinatario,
                "assunto": assunto,
                "corpo": corpo,
            }
        )


def disparar_alerta_fake(
    analise_lote: AnaliseLote,
    classificacao: str,
    destinatario: str,
):
    return disparar_alerta_real(
        analise_lote=analise_lote,
        classificacao=classificacao,
        destinatario=destinatario,
        email_sender=FakeSender(),
    )


def main() -> int:
    codigos = [
        "PROD-001",
        "PROD-002",
        "PROD-003",
        "PROD-004",
        "PROD-005",
        "PROD-006",
    ]

    Alerta.objects.filter(analise_lote__codigo_produto__in=codigos).delete()
    AnaliseLote.objects.filter(codigo_produto__in=codigos).delete()
    ConfiguracaoAlerta.objects.filter(
        destinatario="gestor-mvp@empresa.com"
    ).delete()
    ConfiguracaoAlerta.objects.create(
        classificacao="VENCIDO",
        canal="EMAIL",
        destinatario="gestor-mvp@empresa.com",
        ativo=True,
    )
    ConfiguracaoAlerta.objects.create(
        classificacao="CRITICO",
        canal="EMAIL",
        destinatario="gestor-mvp@empresa.com",
        ativo=True,
    )

    comando_monitoramento.disparar_alerta = disparar_alerta_fake

    saida = StringIO()
    call_command(
        "executar_monitoramento",
        "--fonte",
        "csv",
        "--arquivo",
        "data/lotes_mockados.csv",
        stdout=saida,
    )

    total_analises = AnaliseLote.objects.filter(
        codigo_produto__in=codigos
    ).count()
    total_alertas = Alerta.objects.filter(
        analise_lote__codigo_produto__in=codigos
    ).count()
    classificacoes = list(
        AnaliseLote.objects.filter(codigo_produto__in=codigos)
        .order_by("codigo_produto")
        .values_list("codigo_produto", "lote", "classificacao", "dias_restantes")
    )

    print(saida.getvalue())
    print(f"analises={total_analises}")
    print(f"alertas={total_alertas}")
    print(f"envios_fake={len(FakeSender.envios)}")
    print(f"classificacoes={classificacoes}")

    if total_analises != 6:
        print("ERRO: total de analises diferente de 6.")
        return 1
    if total_alertas != 4:
        print("ERRO: total de alertas diferente de 4.")
        return 1
    if len(FakeSender.envios) != 4:
        print("ERRO: total de envios fake diferente de 4.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
