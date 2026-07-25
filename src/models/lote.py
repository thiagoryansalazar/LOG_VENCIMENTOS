from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Lote:
    codigo_produto: str
    nome_produto: str
    lote: str
    quantidade: Decimal | int | float
    data_validade: date
    local: str

    def __str__(self) -> str:
        return f"{self.codigo_produto} / {self.lote}"
