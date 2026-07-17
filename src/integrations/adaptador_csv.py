import csv
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .base import AdaptadorFonteExterna


class AdaptadorCSV(AdaptadorFonteExterna):
    """Le registros de uma fonte CSV autorizada sem alterar a origem."""

    def __init__(self, caminho_csv: str | Path = "lotes_mockados.csv") -> None:
        self.caminho_csv = self._resolver_caminho(caminho_csv)

    def obter_registros(
        self,
        contexto: Mapping[str, Any] | None = None,
    ) -> Iterable[Mapping[str, Any]]:
        caminho = self.caminho_csv
        if contexto and contexto.get("caminho_csv"):
            caminho = self._resolver_caminho(contexto["caminho_csv"])

        with caminho.open("r", encoding="utf-8", newline="") as arquivo:
            yield from csv.DictReader(arquivo)

    @staticmethod
    def _resolver_caminho(caminho_csv: str | Path) -> Path:
        caminho = Path(caminho_csv)
        if caminho.is_absolute():
            return caminho

        raiz_projeto = Path(__file__).resolve().parents[2]
        if len(caminho.parts) > 1:
            return raiz_projeto / caminho
        return raiz_projeto / "data" / caminho
