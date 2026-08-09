from rest_framework import serializers

from core.models import AnaliseLote, HistoricoLote


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()


class ValidarLoteSerializer(serializers.Serializer):
    codigo_produto = serializers.CharField()
    nome_produto = serializers.CharField()
    lote = serializers.CharField()
    quantidade = serializers.FloatField()
    data_validade = serializers.DateField()
    local = serializers.CharField()


class ErrorSerializer(serializers.Serializer):
    erro = serializers.CharField()
    detalhes = serializers.JSONField()


class ResultadoAlertaSerializer(serializers.Serializer):
    enviado = serializers.BooleanField()
    suprimido = serializers.BooleanField()
    motivo = serializers.CharField()
    alerta_id = serializers.IntegerField(allow_null=True, required=False)


class ResultadoMonitoramentoSerializer(serializers.Serializer):
    valido = serializers.BooleanField()
    dias_restantes = serializers.IntegerField(allow_null=True)
    classificacao = serializers.CharField(allow_null=True)
    erros = serializers.DictField()
    alerta = ResultadoAlertaSerializer(required=False, allow_null=True)


class AnaliseLoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnaliseLote
        fields = (
            "id",
            "nome_produto",
            "codigo_produto",
            "lote",
            "quantidade_inicial",
            "quantidade_atual",
            "data_validade",
            "dias_restantes",
            "classificacao",
            "data_analise",
            "local",
            "unidade",
            "origem",
        )


class ConsultaLoteQuerySerializer(serializers.Serializer):
    codigo_produto = serializers.CharField(required=False, allow_blank=False)
    lote = serializers.CharField(required=False, allow_blank=False)


class DispararAlertaSerializer(serializers.Serializer):
    analise_lote_id = serializers.IntegerField(min_value=1)
    destinatario = serializers.EmailField()


class CadastrarLoteSerializer(serializers.Serializer):
    nome_produto = serializers.CharField(max_length=255, required=False, allow_blank=True)
    codigo_produto = serializers.CharField(max_length=100)
    lote = serializers.CharField(max_length=100)
    quantidade_inicial = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0)
    data_validade = serializers.DateField()
    local = serializers.CharField(required=False, allow_blank=True, max_length=100)
    unidade = serializers.CharField(required=False, allow_blank=True, max_length=50)
    origem = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        default="MANUAL",
    )


class AtualizarLoteSerializer(serializers.Serializer):
    quantidade_atual = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0, required=False)
    local = serializers.CharField(required=False, allow_blank=True, max_length=100)


class HistoricoLoteSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()
    lote = serializers.CharField(source="analise_lote.lote", read_only=True)
    codigo_produto = serializers.CharField(source="analise_lote.codigo_produto", read_only=True)
    nome_produto = serializers.CharField(source="analise_lote.nome_produto", read_only=True)

    class Meta:
        model = HistoricoLote
        fields = (
            "id",
            "analise_lote",
            "codigo_produto",
            "nome_produto",
            "lote",
            "usuario_nome",
            "quantidade_anterior",
            "quantidade_nova",
            "local_anterior",
            "local_novo",
            "criado_em",
        )

    def get_usuario_nome(self, obj) -> str:
        if obj.usuario_id and obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return "Sistema"


class ImportarArquivoSerializer(serializers.Serializer):
    arquivo = serializers.FileField()


class ErroImportacaoSerializer(serializers.Serializer):
    linha = serializers.IntegerField()
    erros = serializers.ListField(child=serializers.CharField())


class ResultadoImportacaoSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    importados = serializers.IntegerField()
    atualizados = serializers.IntegerField()
    invalidos = serializers.IntegerField()
    erros = ErroImportacaoSerializer(many=True)
    tipo_arquivo = serializers.CharField()


class ConfigSistemaSerializer(serializers.Serializer):
    dias_critico = serializers.IntegerField()
    dias_atencao = serializers.IntegerField()
    timezone = serializers.CharField()
    email_alertas_configurado = serializers.BooleanField()
    api_key_requerida = serializers.BooleanField()
    classificacao_descricao = serializers.CharField()
    nome_gestor = serializers.CharField()
    nome_empresa = serializers.CharField()
