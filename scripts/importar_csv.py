from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from src.integrations import AdaptadorCSV, MapeadorCSV  # noqa: E402
from src.services import monitorar_lote  # noqa: E402


def importar_csv(caminho_csv: str, hoje: date) -> Counter[str]:
    adaptador = AdaptadorCSV(caminho_csv)
    mapeador = MapeadorCSV()
    classificacoes: Counter[str] = Counter()

    for indice, registro in enumerate(adaptador.obter_registros(), start=1):
        payload = mapeador.mapear(registro)
        resultado = monitorar_lote(payload, hoje=hoje)
        classificacao = (
            resultado.classificacao.value
            if resultado.classificacao is not None
            else "INVALIDO"
        )
        classificacoes[classificacao] += 1
        print(
            f"Linha {indice}: {payload['codigo_produto']} / {payload['lote']} "
            f"-> {classificacao} ({resultado.dias_restantes} dias)"
        )

    total = sum(classificacoes.values())
    print(f"Total de lotes processados: {total}")
    print("Classificacoes encontradas:")
    for classificacao, quantidade in sorted(classificacoes.items()):
        print(f"- {classificacao}: {quantidade}")

    return classificacoes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa CSV mockado e classifica lotes pelo core."
    )
    parser.add_argument(
        "caminho_csv",
        nargs="?",
        default="lotes_mockados.csv",
        help="Caminho absoluto, relativo ao projeto ou nome de arquivo em data/.",
    )
    args = parser.parse_args()
    importar_csv(args.caminho_csv, hoje=date.today())


if __name__ == "__main__":
    main()
