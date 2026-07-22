from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from itertools import islice
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from core.models import AnaliseLote, ConfiguracaoAlerta
from src.integrations import AdaptadorCSV, MapeadorCSV
from src.services import monitorar_lote
from src.services.alerta import ResultadoAlerta, disparar_alerta
from src.services.vencimento import ClassificacaoRisco

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ResumoMonitoramento:
    lidos: int = 0
    processados: int = 0
    salvos: int = 0
    atualizados: int = 0
    invalidos: int = 0
    erros: int = 0
    alertas_enviados: int = 0
    alertas_suprimidos: int = 0
    alertas_sem_configuracao: int = 0
    alertas_sem_credencial: int = 0


class Command(BaseCommand):
    help = "Executa o monitoramento de lotes a partir de uma fonte externa."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--fonte",
            default="csv",
            choices=["csv"],
            help="Fonte de dados a processar. Atualmente: csv.",
        )
        parser.add_argument(
            "--arquivo",
            default="lotes_mockados.csv",
            help="Caminho absoluto, relativo ao projeto ou arquivo em data/.",
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=None,
            help="Numero maximo de registros a processar.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a execucao sem persistir dados ou disparar alertas.",
        )

    def handle(self, *args, **options) -> None:
        fonte = options["fonte"]
        arquivo = options["arquivo"]
        limite = options["limite"]
        dry_run = options["dry_run"]

        if limite is not None and limite <= 0:
            raise CommandError("--limite deve ser maior que zero.")

        self.stdout.write(
            f"Iniciando monitoramento: fonte={fonte} arquivo={arquivo} "
            f"limite={limite or 'sem_limite'} dry_run={dry_run}"
        )
        logger.info(
            "monitoramento iniciado",
            extra={
                "fonte": fonte,
                "arquivo": arquivo,
                "limite": limite,
                "dry_run": dry_run,
            },
        )

        resumo = self._executar_csv(
            arquivo=arquivo,
            limite=limite,
            dry_run=dry_run,
            hoje=date.today(),
        )

        self._exibir_resumo(resumo)

    def _executar_csv(
        self,
        arquivo: str,
        limite: int | None,
        dry_run: bool,
        hoje: date,
    ) -> ResumoMonitoramento:
        adaptador = AdaptadorCSV(arquivo)
        mapeador = MapeadorCSV()
        registros = adaptador.obter_registros()
        if limite is not None:
            registros = islice(registros, limite)

        resumo = ResumoMonitoramento()

        for linha, registro in enumerate(registros, start=1):
            resumo.lidos += 1
            try:
                payload = mapeador.mapear(registro)
                resultado = monitorar_lote(payload, hoje=hoje)

                if not resultado.valido or resultado.classificacao is None:
                    resumo.invalidos += 1
                    self._log_linha(
                        linha,
                        "invalido",
                        f"erros={resultado.erros}",
                    )
                    continue

                resumo.processados += 1
                if dry_run:
                    self._log_linha(
                        linha,
                        "dry-run",
                        (
                            f"{payload['codigo_produto']} / {payload['lote']} -> "
                            f"{resultado.classificacao.value} "
                            f"({resultado.dias_restantes} dias)"
                        ),
                    )
                    continue

                analise, criado = self._salvar_analise(
                    payload=payload,
                    classificacao=resultado.classificacao.value,
                    dias_restantes=resultado.dias_restantes,
                    origem="CSV",
                )
                if criado:
                    resumo.salvos += 1
                else:
                    resumo.atualizados += 1

                self._log_linha(
                    linha,
                    "persistido",
                    (
                        f"analise_id={analise.id} "
                        f"classificacao={resultado.classificacao.value}"
                    ),
                )
                self._processar_alertas(
                    analise=analise,
                    classificacao=resultado.classificacao,
                    resumo=resumo,
                )

            except Exception as exc:  # noqa: BLE001 - command must keep processing rows.
                resumo.erros += 1
                logger.exception("erro ao processar linha %s", linha)
                self._log_linha(linha, "erro", str(exc))

        return resumo

    def _salvar_analise(
        self,
        payload: dict[str, Any],
        classificacao: str,
        dias_restantes: int | None,
        origem: str,
    ) -> tuple[AnaliseLote, bool]:
        defaults = {
            "data_validade": payload["data_validade"],
            "dias_restantes": dias_restantes,
            "classificacao": classificacao,
            "origem": origem,
        }
        try:
            with transaction.atomic():
                return AnaliseLote.objects.update_or_create(
                    codigo_produto=payload["codigo_produto"],
                    lote=payload["lote"],
                    defaults=defaults,
                )
        except IntegrityError:
            analise = AnaliseLote.objects.get(
                codigo_produto=payload["codigo_produto"],
                lote=payload["lote"],
            )
            for campo, valor in defaults.items():
                setattr(analise, campo, valor)
            analise.save(update_fields=[*defaults.keys()])
            return analise, False

    def _processar_alertas(
        self,
        analise: AnaliseLote,
        classificacao: ClassificacaoRisco,
        resumo: ResumoMonitoramento,
    ) -> None:
        if classificacao not in {
            ClassificacaoRisco.CRITICO,
            ClassificacaoRisco.VENCIDO,
        }:
            return

        configuracoes = ConfiguracaoAlerta.objects.filter(
            classificacao=classificacao.value,
            canal__iexact="EMAIL",
            ativo=True,
        )
        if not configuracoes.exists():
            resumo.alertas_sem_configuracao += 1
            self.stdout.write(
                f"Alerta sem configuracao: analise_id={analise.id} "
                f"classificacao={classificacao.value}"
            )
            return

        for configuracao in configuracoes:
            try:
                resultado_alerta = disparar_alerta(
                    analise_lote=analise,
                    classificacao=classificacao.value,
                    destinatario=configuracao.destinatario,
                )
            except RuntimeError as exc:
                resumo.alertas_sem_credencial += 1
                logger.warning(
                    "alerta pulado por falha operacional: analise_id=%s erro=%s",
                    analise.id,
                    exc,
                )
                self.stdout.write(
                    f"Alerta pulado sem credencial: analise_id={analise.id} "
                    f"destinatario={configuracao.destinatario}"
                )
                continue
            self._contabilizar_alerta(resultado_alerta, resumo)
            self.stdout.write(
                f"Alerta: analise_id={analise.id} "
                f"destinatario={configuracao.destinatario} "
                f"resultado={resultado_alerta.motivo}"
            )

    @staticmethod
    def _contabilizar_alerta(
        resultado_alerta: ResultadoAlerta,
        resumo: ResumoMonitoramento,
    ) -> None:
        if resultado_alerta.enviado:
            resumo.alertas_enviados += 1
        elif resultado_alerta.suprimido:
            resumo.alertas_suprimidos += 1

    def _log_linha(self, linha: int, status: str, detalhe: str) -> None:
        mensagem = f"Linha {linha}: {status} - {detalhe}"
        logger.info(mensagem)
        self.stdout.write(mensagem)

    def _exibir_resumo(self, resumo: ResumoMonitoramento) -> None:
        self.stdout.write("Resumo do monitoramento:")
        self.stdout.write(f"- lidos: {resumo.lidos}")
        self.stdout.write(f"- processados: {resumo.processados}")
        self.stdout.write(f"- salvos: {resumo.salvos}")
        self.stdout.write(f"- atualizados: {resumo.atualizados}")
        self.stdout.write(f"- invalidos: {resumo.invalidos}")
        self.stdout.write(f"- erros: {resumo.erros}")
        self.stdout.write(f"- alertas_enviados: {resumo.alertas_enviados}")
        self.stdout.write(f"- alertas_suprimidos: {resumo.alertas_suprimidos}")
        self.stdout.write(
            f"- alertas_sem_configuracao: {resumo.alertas_sem_configuracao}"
        )
        self.stdout.write(f"- alertas_sem_credencial: {resumo.alertas_sem_credencial}")
