from __future__ import annotations

from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from core.models import Alerta, AnaliseLote, ConfiguracaoAlerta
from src.services.alerta import ResultadoAlerta


class ExecutarMonitoramentoCommandTests(TestCase):
    def criar_csv(self, linhas: list[dict[str, str]]) -> str:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        caminho = Path(temp_dir.name) / "lotes.csv"
        cabecalho = [
            "codigo_produto",
            "nome_produto",
            "lote",
            "quantidade",
            "data_validade",
            "local",
        ]
        conteudo = [",".join(cabecalho)]
        for linha in linhas:
            conteudo.append(",".join(linha.get(campo, "") for campo in cabecalho))
        caminho.write_text("\n".join(conteudo), encoding="utf-8")
        return str(caminho)

    def linha_valida(
        self,
        codigo_produto: str = "PROD-CMD-001",
        lote: str = "LOTE-CMD-001",
        dias: int = 3,
    ) -> dict[str, str]:
        return {
            "codigo_produto": codigo_produto,
            "nome_produto": "Leite Integral",
            "lote": lote,
            "quantidade": "10",
            "data_validade": (date.today() + timedelta(days=dias)).isoformat(),
            "local": "CD Teste",
        }

    def test_dry_run_nao_persiste_nem_dispara_alerta(self) -> None:
        caminho_csv = self.criar_csv([self.linha_valida()])
        saida = StringIO()

        with patch(
            "core.management.commands.executar_monitoramento.disparar_alerta"
        ) as disparar_mock:
            call_command(
                "executar_monitoramento",
                "--fonte",
                "csv",
                "--arquivo",
                caminho_csv,
                "--dry-run",
                stdout=saida,
            )

        self.assertIn("dry-run", saida.getvalue())
        self.assertIn("- salvos: 0", saida.getvalue())
        self.assertEqual(AnaliseLote.objects.count(), 0)
        self.assertEqual(Alerta.objects.count(), 0)
        disparar_mock.assert_not_called()

    def test_execucao_real_persiste_e_dispara_alerta_mockado(self) -> None:
        ConfiguracaoAlerta.objects.create(
            classificacao="CRITICO",
            canal="EMAIL",
            destinatario="gestor@empresa.com",
            ativo=True,
        )
        caminho_csv = self.criar_csv([self.linha_valida(dias=3)])
        saida = StringIO()

        with patch(
            "core.management.commands.executar_monitoramento.disparar_alerta",
            return_value=ResultadoAlerta(
                enviado=True,
                suprimido=False,
                motivo="alerta enviado",
                alerta_id=123,
            ),
        ) as disparar_mock:
            call_command(
                "executar_monitoramento",
                "--fonte",
                "csv",
                "--arquivo",
                caminho_csv,
                stdout=saida,
            )

        self.assertEqual(AnaliseLote.objects.count(), 1)
        analise = AnaliseLote.objects.get()
        self.assertEqual(analise.classificacao, "CRITICO")
        disparar_mock.assert_called_once()
        self.assertIn("- salvos: 1", saida.getvalue())
        self.assertIn("- alertas_enviados: 1", saida.getvalue())

    def test_limite_restringe_total_de_registros_processados(self) -> None:
        caminho_csv = self.criar_csv(
            [
                self.linha_valida("PROD-CMD-001", "LOTE-CMD-001", 40),
                self.linha_valida("PROD-CMD-002", "LOTE-CMD-002", 40),
            ]
        )
        saida = StringIO()

        call_command(
            "executar_monitoramento",
            "--fonte",
            "csv",
            "--arquivo",
            caminho_csv,
            "--limite",
            "1",
            stdout=saida,
        )

        self.assertEqual(AnaliseLote.objects.count(), 1)
        self.assertIn("- lidos: 1", saida.getvalue())
        self.assertIn("- processados: 1", saida.getvalue())

    def test_erro_por_linha_nao_interrompe_processamento(self) -> None:
        linha_invalida = self.linha_valida("PROD-CMD-INV", "LOTE-CMD-INV")
        linha_invalida["quantidade"] = "abc"
        caminho_csv = self.criar_csv(
            [
                linha_invalida,
                self.linha_valida("PROD-CMD-OK", "LOTE-CMD-OK", 40),
            ]
        )
        saida = StringIO()

        call_command(
            "executar_monitoramento",
            "--fonte",
            "csv",
            "--arquivo",
            caminho_csv,
            stdout=saida,
        )

        self.assertEqual(AnaliseLote.objects.count(), 1)
        self.assertIn("Linha 1: erro", saida.getvalue())
        self.assertIn("- erros: 1", saida.getvalue())
        self.assertIn("- salvos: 1", saida.getvalue())

    def test_alerta_sem_credencial_nao_falha_processamento(self) -> None:
        ConfiguracaoAlerta.objects.create(
            classificacao="CRITICO",
            canal="EMAIL",
            destinatario="gestor@empresa.com",
            ativo=True,
        )
        caminho_csv = self.criar_csv([self.linha_valida(dias=3)])
        saida = StringIO()

        with patch(
            "core.management.commands.executar_monitoramento.disparar_alerta",
            side_effect=RuntimeError("Credenciais de email ausentes."),
        ):
            call_command(
                "executar_monitoramento",
                "--fonte",
                "csv",
                "--arquivo",
                caminho_csv,
                stdout=saida,
            )

        self.assertEqual(AnaliseLote.objects.count(), 1)
        self.assertIn("- erros: 0", saida.getvalue())
        self.assertIn("- alertas_sem_credencial: 1", saida.getvalue())
