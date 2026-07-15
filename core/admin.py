from django.contrib import admin

from .models import Alerta, AnaliseLote, ConfiguracaoAlerta


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
    search_fields = ("destinatario",)
