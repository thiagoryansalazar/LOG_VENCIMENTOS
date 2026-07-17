from collections.abc import Mapping
from datetime import date
from typing import Any

from .mapeamento import MapeadorCampos


class MapeadorCSV(MapeadorCampos):
    """Mapeia registros CSV para o payload canonico do ATLAS."""

    CAMPOS_OBRIGATORIOS = (
        "codigo_produto",
        "nome_produto",
        "lote",
        "quantidade",
        "data_validade",
        "local",
    )

    def mapear(self, registro: Mapping[str, Any]) -> dict[str, Any]:
        faltantes = [
            campo
            for campo in self.CAMPOS_OBRIGATORIOS
            if not str(registro.get(campo, "")).strip()
        ]
        if faltantes:
            raise ValueError(
                "Campos obrigatorios ausentes ou vazios: "
                + ", ".join(faltantes)
            )

        return {
            "codigo_produto": str(registro["codigo_produto"]).strip(),
            "nome_produto": str(registro["nome_produto"]).strip(),
            "lote": str(registro["lote"]).strip(),
            "quantidade": self._converter_quantidade(registro["quantidade"]),
            "data_validade": self._converter_data(registro["data_validade"]),
            "local": str(registro["local"]).strip(),
        }

    @staticmethod
    def _converter_quantidade(valor: Any) -> int | float:
        texto = str(valor).strip().replace(",", ".")
        try:
            numero = float(texto)
        except ValueError as exc:
            raise ValueError("Campo quantidade deve ser numerico.") from exc

        return int(numero) if numero.is_integer() else numero

    @staticmethod
    def _converter_data(valor: Any) -> date:
        try:
            return date.fromisoformat(str(valor).strip())
        except ValueError as exc:
            raise ValueError(
                "Campo data_validade deve estar no formato YYYY-MM-DD."
            ) from exc
