from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from src.services import monitorar_lote


@api_view(["GET"])
def health(request: Request) -> Response:
    return Response({"status": "ok"})


@api_view(["POST"])
def validar_lote_view(request: Request) -> Response:
    resultado = monitorar_lote(request.data, hoje=date.today())
    return Response(
        resultado.para_resposta(),
        status=(
            status.HTTP_200_OK
            if resultado.valido
            else status.HTTP_400_BAD_REQUEST
        ),
    )
