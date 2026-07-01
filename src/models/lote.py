from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Lote:
    codigo_produto: str
    nome_produto: str
    lote: str
    quantidade: int | float | Decimal
    data_validade: date
    local: str
