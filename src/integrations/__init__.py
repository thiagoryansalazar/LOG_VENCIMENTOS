"""Conectores para fontes externas autorizadas."""

from .adaptador_csv import AdaptadorCSV
from .base import AdaptadorFonteExterna, ModoIntegracao
from .erp import AdaptadorConsultaERP
from .mapeador_csv import MapeadorCSV
from .mapeamento import MapeadorCampos

__all__ = [
    "AdaptadorCSV",
    "AdaptadorConsultaERP",
    "AdaptadorFonteExterna",
    "MapeadorCSV",
    "MapeadorCampos",
    "ModoIntegracao",
]
