from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class MapeadorCampos(ABC):
    """Traduz um registro externo para o payload canonico do LOG."""

    @abstractmethod
    def mapear(self, registro: Mapping[str, Any]) -> dict[str, Any]:
        """Mapeia campos sem validar regras de negocio."""
