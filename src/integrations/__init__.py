"""Conectores para fontes externas autorizadas."""

from .base import AdaptadorFonteExterna, ModoIntegracao
from .erp import AdaptadorConsultaERP
from .mapeamento import MapeadorCampos

__all__ = [
    "AdaptadorConsultaERP",
    "AdaptadorFonteExterna",
    "MapeadorCampos",
    "ModoIntegracao",
]
