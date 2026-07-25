from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.models import AnaliseLote
from src.services import disparar_alerta, monitorar_lote

from .serializers import (
    AnaliseLoteSerializer,
    ConsultaLoteQuerySerializer,
    DispararAlertaSerializer,
    ErrorSerializer,
    HealthSerializer,
    ResultadoAlertaSerializer,
    ResultadoMonitoramentoSerializer,
    ValidarLoteSerializer,
)


@extend_schema(responses=HealthSerializer)
@api_view(["GET"])
def health(request: Request) -> Response:
    return Response({"status": "ok"})


@extend_schema(
    request=ValidarLoteSerializer,
    responses={
        200: ResultadoMonitoramentoSerializer,
        400: ResultadoMonitoramentoSerializer,
    },
)
@api_view(["POST"])
def validar_lote_view(request: Request) -> Response:
    serializer = ValidarLoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "valido": False,
                "dias_restantes": None,
                "classificacao": None,
                "erros": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    resultado = monitorar_lote(serializer.validated_data, hoje=date.today())
    return Response(
        resultado.para_resposta(),
        status=(
            status.HTTP_200_OK
            if resultado.valido
            else status.HTTP_400_BAD_REQUEST
        ),
    )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="codigo_produto",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name="lote",
            required=False,
            type=str,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses=AnaliseLoteSerializer(many=True),
)
@api_view(["GET"])
def listar_lotes_view(request: Request) -> Response:
    query_serializer = ConsultaLoteQuerySerializer(data=request.query_params)
    if not query_serializer.is_valid():
        return Response(
            {"erro": "Parametros invalidos.", "detalhes": query_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    analises = AnaliseLote.objects.all()
    codigo_produto = query_serializer.validated_data.get("codigo_produto")
    lote = query_serializer.validated_data.get("lote")

    if codigo_produto:
        analises = analises.filter(codigo_produto=codigo_produto)
    if lote:
        analises = analises.filter(lote=lote)

    return Response(AnaliseLoteSerializer(analises, many=True).data)


@extend_schema(responses=AnaliseLoteSerializer(many=True))
@api_view(["GET"])
def listar_lotes_criticos_view(request: Request) -> Response:
    analises = AnaliseLote.objects.filter(
        classificacao__in=["CRITICO", "VENCIDO"],
    )

    return Response(AnaliseLoteSerializer(analises, many=True).data)


@extend_schema(
    request=DispararAlertaSerializer,
    responses={
        200: ResultadoAlertaSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
        500: ErrorSerializer,
    },
)
@api_view(["POST"])
def disparar_alerta_manual_view(request: Request) -> Response:
    serializer = DispararAlertaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Payload invalido.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    analise = AnaliseLote.objects.filter(
        id=serializer.validated_data["analise_lote_id"],
    ).first()
    if analise is None:
        return Response(
            {"erro": "AnaliseLote nao encontrado.", "detalhes": {}},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        resultado = disparar_alerta(
            analise_lote=analise,
            classificacao=analise.classificacao,
            destinatario=serializer.validated_data["destinatario"],
        )
    except RuntimeError as exc:
        return Response(
            {"erro": "Falha operacional ao disparar alerta.", "detalhes": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(ResultadoAlertaSerializer(resultado.para_resposta()).data)
