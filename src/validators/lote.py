import math
from datetime import date
from decimal import Decimal
from typing import Any

from src.models import Lote


REQUIRED_TEXT_FIELDS = (
    "codigo_produto",
    "nome_produto",
    "lote",
    "local",
)
MAX_TEXT_LENGTH = 255


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validar_lote(payload: Any) -> tuple[Lote | None, dict[str, list[str]]]:
    errors: dict[str, list[str]] = {}

    if not isinstance(payload, dict):
        return None, {"payload": ["O corpo da requisicao deve ser um objeto JSON."]}

    text_values: dict[str, str] = {}
    for field in REQUIRED_TEXT_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors[field] = ["Este campo e obrigatorio e deve ser um texto."]
        elif len(value.strip()) > MAX_TEXT_LENGTH:
            errors[field] = [
                f"Este campo deve ter no maximo {MAX_TEXT_LENGTH} caracteres."
            ]
        else:
            text_values[field] = value.strip()

    if "quantidade" not in payload:
        errors["quantidade"] = ["Este campo e obrigatorio."]
    else:
        quantidade = payload.get("quantidade")
        if isinstance(quantidade, bool):
            errors["quantidade"] = ["Valor booleano nao e aceito como quantidade."]
        elif not isinstance(quantidade, (int, float, Decimal)):
            errors["quantidade"] = ["Deve ser um valor numerico."]
        elif not math.isfinite(quantidade):
            errors["quantidade"] = ["Deve ser um numero finito."]
        elif quantidade <= 0:
            errors["quantidade"] = ["Deve ser maior que zero."]

    data_validade = _parse_date(payload.get("data_validade"))
    if data_validade is None:
        errors["data_validade"] = [
            "Informe uma data valida no formato ISO YYYY-MM-DD."
        ]

    if errors:
        return None, errors

    lote = Lote(
        codigo_produto=text_values["codigo_produto"],
        nome_produto=text_values["nome_produto"],
        lote=text_values["lote"],
        quantidade=payload["quantidade"],
        data_validade=data_validade,
        local=text_values["local"],
    )
    return lote, {}
