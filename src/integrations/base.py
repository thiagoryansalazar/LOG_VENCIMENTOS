from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from enum import StrEnum
from typing import Any


class ModoIntegracao(StrEnum):
    EVENTO = "EVENTO"
    CONSULTA_AGENDADA = "CONSULTA_AGENDADA"
    ARQUIVO = "ARQUIVO"


class AdaptadorFonteExterna(ABC):
    """Porta de leitura compartilhada pelos diferentes sistemas de origem."""

    @abstractmethod
    def obter_registros(
        self,
        contexto: Mapping[str, Any] | None = None,
    ) -> Iterable[Mapping[str, Any]]:
        """Obtem dados sem alterar a fonte oficial.

        O contexto pode carregar informacoes de acionamento por evento,
        agendamento ou arquivo sem definir prematuramente um payload canonico.
        """
