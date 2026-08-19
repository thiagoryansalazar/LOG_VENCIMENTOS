from django.contrib import admin

from .models import Alerta, AnaliseLote, ConexaoSistema, ConfiguracaoAlerta, EventoOperacional, HistoricoLote


@admin.register(AnaliseLote)
class AnaliseLoteAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_produto",
        "lote",
        "classificacao",
        "dias_restantes",
        "data_validade",
        "origem",
        "data_analise",
    )
    list_filter = ("classificacao", "origem", "data_analise")
    search_fields = ("codigo_produto", "lote")


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = (
        "analise_lote",
        "classificacao",
        "destinatario",
        "enviado_em",
    )
    list_filter = ("classificacao", "enviado_em")
    search_fields = (
        "analise_lote__codigo_produto",
        "analise_lote__lote",
        "destinatario",
    )


@admin.register(ConfiguracaoAlerta)
class ConfiguracaoAlertaAdmin(admin.ModelAdmin):
    list_display = ("classificacao", "canal", "destinatario", "ativo")
    list_filter = ("classificacao", "canal", "ativo")


@admin.register(HistoricoLote)
class HistoricoLoteAdmin(admin.ModelAdmin):
    list_display = ("analise_lote", "usuario", "quantidade_anterior", "quantidade_nova", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("analise_lote__codigo_produto", "analise_lote__lote", "usuario__username")


@admin.register(EventoOperacional)
class EventoOperacionalAdmin(admin.ModelAdmin):
    list_display = ("tipo", "usuario", "total_lotes", "criado_em")
    list_filter = ("tipo", "criado_em")
    search_fields = ("tipo", "descricao", "usuario__username")


@admin.register(ConexaoSistema)
class ConexaoSistemaAdmin(admin.ModelAdmin):
    list_display = ("nome_sistema", "criado_em", "atualizado_em")
    readonly_fields = ("api_url_encrypted", "webhook_url_encrypted", "criado_em", "atualizado_em")
