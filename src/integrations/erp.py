from abc import abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any

from .base import AdaptadorFonteExterna


class AdaptadorConsultaERP(AdaptadorFonteExterna):
    """Porta de leitura para o repositorio de lotes mantido pelo ERP."""

    @abstractmethod
    def consultar_lotes(self) -> Iterable[Mapping[str, Any]]:
        """Inicia uma consulta autorizada e deve ser implementada por fonte."""
        raise NotImplementedError

    def obter_registros(
        self,
        contexto: Mapping[str, Any] | None = None,
    ) -> Iterable[Mapping[str, Any]]:
        """Converte a porta generica na consulta de lotes do ERP."""
        return self.consultar_lotes()
