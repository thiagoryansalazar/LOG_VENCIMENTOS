from datetime import date

from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.models import AnaliseLote, ConexaoSistema, EventoOperacional, HistoricoLote
from src.services import disparar_alerta, monitorar_lote
from src.services.importacao import processar_importacao
from src.services.vencimento import (
    calcular_dias_restantes,
    classificar_risco,
)

from .serializers import (
    AnaliseLoteSerializer,
    AtualizarLoteSerializer,
    CadastrarLoteSerializer,
    ConexaoSistemaCriacaoSerializer,
    ConexaoSistemaEntradaSerializer,
    ConexaoSistemaSerializer,
    ConfigSistemaSerializer,
    ConsultaLoteQuerySerializer,
    DispararAlertaSerializer,
    ErrorSerializer,
    EventoOperacionalSerializer,
    HealthSerializer,
    HistoricoLoteSerializer,
    ImportarArquivoSerializer,
    ResultadoAlertaSerializer,
    ResultadoImportacaoSerializer,
    ResultadoMonitoramentoSerializer,
    ValidarLoteSerializer,
)
from src.services.segredos import criptografar, descriptografar, mascarar_url


def _usuario_autenticado(request: Request):
    user = getattr(request, "user", None)
    return user if getattr(user, "is_authenticated", False) else None


def _registrar_historico(analise: AnaliseLote, usuario, quantidade_anterior, local_anterior):
    if analise.quantidade_atual == quantidade_anterior and analise.local == local_anterior:
        return
    HistoricoLote.objects.create(
        analise_lote=analise,
        usuario=usuario,
        quantidade_anterior=quantidade_anterior,
        quantidade_nova=analise.quantidade_atual,
        local_anterior=local_anterior or "",
        local_novo=analise.local or "",
    )


def _registrar_evento(tipo: str, descricao: str, usuario=None, total_lotes: int | None = None):
    EventoOperacional.objects.create(
        tipo=tipo,
        descricao=descricao,
        usuario=usuario,
        total_lotes=total_lotes,
    )


def _conexao_sistema_payload(conexao: ConexaoSistema) -> dict:
    api_url = descriptografar(conexao.api_url_encrypted)
    webhook_url = descriptografar(conexao.webhook_url_encrypted)
    return {
        "id": conexao.id,
        "nome_sistema": conexao.nome_sistema,
        "api_url_mascarada": mascarar_url(api_url),
        "webhook_url_mascarada": mascarar_url(webhook_url),
        "api_url_configurada": bool(api_url),
        "webhook_url_configurada": bool(webhook_url),
        "criado_em": conexao.criado_em,
        "atualizado_em": conexao.atualizado_em,
    }


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

    analises = AnaliseLote.objects.filter(quantidade_atual__gt=0)
    codigo_produto = query_serializer.validated_data.get("codigo_produto")
    lote = query_serializer.validated_data.get("lote")

    if codigo_produto:
        analises = analises.filter(codigo_produto=codigo_produto)
    if lote:
        analises = analises.filter(lote=lote)

    total = analises.count()
    _registrar_evento(
        "BUSCA_LOTES",
        f"Ultima busca feita com {total} lote(s) monitorado(s).",
        _usuario_autenticado(request),
        total,
    )
    return Response(AnaliseLoteSerializer(analises, many=True).data)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="id",
            required=True,
            type=int,
            location=OpenApiParameter.PATH,
        ),
    ],
    responses={
        200: AnaliseLoteSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["GET"])
def consultar_lote_por_id_view(request: Request, id: int) -> Response:
    try:
        analise = AnaliseLote.objects.get(id=id)
    except AnaliseLote.DoesNotExist:
        return Response(
            {"erro": "AnaliseLote nao encontrado.", "detalhes": {}},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(AnaliseLoteSerializer(analise).data)


@extend_schema(
    request=AtualizarLoteSerializer,
    responses={
        200: AnaliseLoteSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    },
)
@api_view(["PATCH"])
def atualizar_lote_view(request: Request, id: int) -> Response:
    analise = AnaliseLote.objects.filter(id=id).first()
    if analise is None:
        return Response(
            {"erro": "AnaliseLote nao encontrado.", "detalhes": {}},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = AtualizarLoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Payload invalido.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    dados = serializer.validated_data
    quantidade_nova = dados.get("quantidade_atual", analise.quantidade_atual)
    if quantidade_nova > analise.quantidade_atual:
        return Response(
            {
                "erro": "Quantidade atual nao pode ser aumentada por edicao manual.",
                "detalhes": {"quantidade_atual": ["Informe um valor menor ou igual ao atual."]},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    quantidade_anterior = analise.quantidade_atual
    local_anterior = analise.local
    analise.quantidade_atual = quantidade_nova
    if "local" in dados:
        analise.local = dados.get("local") or ""
    analise.save(update_fields=["quantidade_atual", "local", "data_analise"])
    _registrar_historico(analise, _usuario_autenticado(request), quantidade_anterior, local_anterior)
    _registrar_evento(
        "ALTERACAO_LOTE",
        f"Lote {analise.lote} alterado de {quantidade_anterior} para {analise.quantidade_atual}.",
        _usuario_autenticado(request),
    )

    return Response(AnaliseLoteSerializer(analise).data)


@extend_schema(responses=HistoricoLoteSerializer(many=True))
@api_view(["GET"])
def listar_historico_lote_view(request: Request, id: int) -> Response:
    if not AnaliseLote.objects.filter(id=id).exists():
        return Response(
            {"erro": "AnaliseLote nao encontrado.", "detalhes": {}},
            status=status.HTTP_404_NOT_FOUND,
        )
    historico = HistoricoLote.objects.filter(analise_lote_id=id).select_related("analise_lote", "usuario")
    return Response(HistoricoLoteSerializer(historico, many=True).data)


@extend_schema(responses=HistoricoLoteSerializer(many=True))
@api_view(["GET"])
def listar_historico_alteracoes_view(request: Request) -> Response:
    historico = EventoOperacional.objects.select_related("usuario")[:100]
    return Response(EventoOperacionalSerializer(historico, many=True).data)


@extend_schema(responses=AnaliseLoteSerializer(many=True))
@api_view(["GET"])
def listar_historico_lotes_monitorados_view(request: Request) -> Response:
    analises = AnaliseLote.objects.filter(quantidade_atual=0)
    return Response(AnaliseLoteSerializer(analises, many=True).data)


@extend_schema(responses=AnaliseLoteSerializer(many=True))
@api_view(["GET"])
def listar_lotes_criticos_view(request: Request) -> Response:
    analises = AnaliseLote.objects.filter(
        quantidade_atual__gt=0,
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


@extend_schema(
    request=CadastrarLoteSerializer,
    responses={
        201: AnaliseLoteSerializer,
        200: AnaliseLoteSerializer,
        400: ErrorSerializer,
    },
)
@api_view(["POST"])
def cadastrar_lote_view(request: Request) -> Response:
    """Cadastra uma analise de lote manualmente, classificando no servidor."""
    serializer = CadastrarLoteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Payload invalido.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    dados = serializer.validated_data
    hoje = date.today()
    dias_restantes = calcular_dias_restantes(dados["data_validade"], hoje)
    classificacao = classificar_risco(dados["data_validade"], hoje)

    try:
        with transaction.atomic():
            existente = AnaliseLote.objects.filter(
                codigo_produto=dados["codigo_produto"],
                lote=dados["lote"],
            ).first()
            quantidade_anterior = existente.quantidade_atual if existente else None
            local_anterior = existente.local if existente else ""
            analise, criado = AnaliseLote.objects.update_or_create(
                codigo_produto=dados["codigo_produto"],
                lote=dados["lote"],
                defaults={
                    "nome_produto": dados.get("nome_produto") or "",
                    "quantidade_inicial": dados["quantidade_inicial"],
                    "quantidade_atual": dados["quantidade_inicial"],
                    "data_validade": dados["data_validade"],
                    "dias_restantes": dias_restantes,
                    "classificacao": classificacao.value,
                    "local": dados.get("local") or "",
                    "unidade": dados.get("unidade") or "",
                    "origem": dados.get("origem") or "MANUAL",
                },
            )
            if not criado:
                _registrar_historico(
                    analise,
                    _usuario_autenticado(request),
                    quantidade_anterior,
                    local_anterior,
                )
            _registrar_evento(
                "CADASTRO_MANUAL" if criado else "ATUALIZACAO_CADASTRO",
                f"Lote {analise.lote} cadastrado com {analise.quantidade_atual} unidade(s).",
                _usuario_autenticado(request),
            )
    except IntegrityError:
        return Response(
            {"erro": "Nao foi possivel cadastrar o lote.", "detalhes": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        AnaliseLoteSerializer(analise).data,
        status=(
            status.HTTP_201_CREATED if criado else status.HTTP_200_OK
        ),
    )


@extend_schema(
    request=ImportarArquivoSerializer,
    responses={
        200: ResultadoImportacaoSerializer,
        400: ErrorSerializer,
    },
)
@api_view(["POST"])
def importar_lotes_view(request: Request) -> Response:
    """Importa lotes a partir de um arquivo comum (CSV, Excel, JSON, TXT)."""
    serializer = ImportarArquivoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Arquivo ausente ou invalido.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    arquivo = serializer.validated_data["arquivo"]
    try:
        resumo = processar_importacao(
            nome=arquivo.name or "",
            conteudo=arquivo.read(),
        )
    except ValueError as exc:
        return Response(
            {"erro": str(exc), "detalhes": {}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(ResultadoImportacaoSerializer(resumo).data)


@extend_schema(responses=ConfigSistemaSerializer)
@api_view(["GET"])
def config_sistema_view(request: Request) -> Response:
    """Configuracoes do servidor em modo somente leitura.

    Os limites de classificacao sao definidos no ambiente do backend
    (DIAS_CRITICO / DIAS_ATENCAO) e nao podem ser alterados por esta rota.
    """
    descricao = (
        "VENCIDO: 0 dias ou menos | CRITICO: 1 a {critico} dias | "
        "ATENCAO: {critico}+1 a {atencao} dias | NORMAL: acima de {atencao} dias"
    ).format(critico=settings.DIAS_CRITICO, atencao=settings.DIAS_ATENCAO)

    return Response(
        {
            "dias_critico": settings.DIAS_CRITICO,
            "dias_atencao": settings.DIAS_ATENCAO,
            "timezone": str(settings.TIME_ZONE),
            "email_alertas_configurado": bool(settings.EMAIL_HOST_USER),
            "api_key_requerida": True,
            "classificacao_descricao": descricao,
            "nome_gestor": settings.ATLAS_GESTOR_NOME,
            "nome_empresa": settings.ATLAS_EMPRESA_NOME,
        }
    )


@extend_schema(
    request=ConexaoSistemaCriacaoSerializer,
    responses={
        200: ConexaoSistemaSerializer(many=True),
        201: ConexaoSistemaSerializer,
        400: ErrorSerializer,
    },
)
@api_view(["GET", "POST"])
def conexoes_sistema_view(request: Request) -> Response:
    if request.method == "GET":
        conexoes = ConexaoSistema.objects.all()
        return Response([_conexao_sistema_payload(conexao) for conexao in conexoes])

    if ConexaoSistema.objects.count() >= ConexaoSistema.MAX_CONEXOES:
        return Response(
            {"erro": f"Limite de {ConexaoSistema.MAX_CONEXOES} sistemas conectados atingido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ConexaoSistemaCriacaoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Dados de conexao invalidos.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    dados = serializer.validated_data
    conexao = ConexaoSistema.objects.create(
        nome_sistema=dados.get("nome_sistema", ""),
        api_url_encrypted=criptografar(dados.get("api_url", "")),
        webhook_url_encrypted=criptografar(dados.get("webhook_url", "")),
    )
    _registrar_evento(
        "CONEXAO_SISTEMA_CRIADA",
        f"Conexao do sistema {conexao.nome_sistema or 'do cliente'} adicionada com dados protegidos.",
        _usuario_autenticado(request),
    )
    return Response(_conexao_sistema_payload(conexao), status=status.HTTP_201_CREATED)


@extend_schema(
    request=ConexaoSistemaEntradaSerializer,
    responses={200: ConexaoSistemaSerializer, 204: None, 400: ErrorSerializer, 404: ErrorSerializer},
)
@api_view(["PATCH", "DELETE"])
def conexao_sistema_detail_view(request: Request, id: int) -> Response:
    try:
        conexao = ConexaoSistema.objects.get(id=id)
    except ConexaoSistema.DoesNotExist:
        return Response({"erro": "Conexao nao encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        nome = conexao.nome_sistema
        conexao.delete()
        _registrar_evento(
            "CONEXAO_SISTEMA_REMOVIDA",
            f"Conexao do sistema {nome or 'do cliente'} removida.",
            _usuario_autenticado(request),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ConexaoSistemaEntradaSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"erro": "Dados de conexao invalidos.", "detalhes": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # So grava o que veio no payload: sobrescrever com vazio um campo que o
    # operador nem tocou apagaria um segredo ja salvo (ex.: editar so o nome
    # do sistema nao pode zerar a API/webhook ja configurados).
    dados = serializer.validated_data
    campos_atualizados = ["atualizado_em"]
    if "nome_sistema" in request.data:
        conexao.nome_sistema = dados.get("nome_sistema", "")
        campos_atualizados.append("nome_sistema")
    if "api_url" in request.data:
        conexao.api_url_encrypted = criptografar(dados.get("api_url", ""))
        campos_atualizados.append("api_url_encrypted")
    if "webhook_url" in request.data:
        conexao.webhook_url_encrypted = criptografar(dados.get("webhook_url", ""))
        campos_atualizados.append("webhook_url_encrypted")

    conexao.save(update_fields=campos_atualizados)
    _registrar_evento(
        "CONEXAO_SISTEMA_ATUALIZADA",
        f"Conexao do sistema {conexao.nome_sistema or 'do cliente'} atualizada com dados protegidos.",
        _usuario_autenticado(request),
    )
    return Response(_conexao_sistema_payload(conexao))
