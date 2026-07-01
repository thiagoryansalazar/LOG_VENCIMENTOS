from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any


class AdaptadorConsultaERP(ABC):
    """Porta de leitura para o repositorio de lotes mantido pelo ERP."""

    @abstractmethod
    def consultar_lotes(self) -> Iterable[Mapping[str, Any]]:
        """Inicia uma consulta autorizada e nao altera a fonte externa."""
