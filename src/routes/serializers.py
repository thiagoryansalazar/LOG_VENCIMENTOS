from rest_framework import serializers

from core.models import AnaliseLote


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
            "codigo_produto",
            "lote",
            "data_validade",
            "dias_restantes",
            "classificacao",
            "data_analise",
            "origem",
        )


class ConsultaLoteQuerySerializer(serializers.Serializer):
    codigo_produto = serializers.CharField(required=False, allow_blank=False)
    lote = serializers.CharField(required=False, allow_blank=False)


class DispararAlertaSerializer(serializers.Serializer):
    analise_lote_id = serializers.IntegerField(min_value=1)
    destinatario = serializers.EmailField()

