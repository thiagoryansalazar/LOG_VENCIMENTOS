from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from src.services import calcular_dias_restantes, classificar_risco
from src.validators import validar_lote


@api_view(["GET"])
def health(request: Request) -> Response:
    return Response({"status": "ok"})


@api_view(["POST"])
def validar_lote_view(request: Request) -> Response:
    lote, errors = validar_lote(request.data)

    if lote is None:
        return Response(
            {
                "valido": False,
                "dias_restantes": None,
                "classificacao": None,
                "erros": errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "valido": True,
            "dias_restantes": calcular_dias_restantes(lote.data_validade),
            "classificacao": classificar_risco(lote.data_validade).value,
            "erros": {},
        }
    )
