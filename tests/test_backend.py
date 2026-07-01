from datetime import date, timedelta

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APISimpleTestCase

from src.integrations import AdaptadorConsultaERP
from src.services import (
    ClassificacaoRisco,
    calcular_dias_restantes,
    classificar_risco,
    monitorar_lote,
)
from src.validators import validar_lote


class VencimentoServiceTests(SimpleTestCase):
    def test_classifica_as_quatro_faixas_de_risco(self) -> None:
        hoje = date(2026, 6, 30)
        casos = (
            (-1, ClassificacaoRisco.VENCIDO),
            (0, ClassificacaoRisco.VENCIDO),
            (1, ClassificacaoRisco.CRITICO),
            (5, ClassificacaoRisco.CRITICO),
            (20, ClassificacaoRisco.ATENCAO),
            (60, ClassificacaoRisco.NORMAL),
        )

        for dias, esperado in casos:
            with self.subTest(dias=dias):
                validade = hoje + timedelta(days=dias)
                self.assertEqual(calcular_dias_restantes(validade, hoje), dias)
                self.assertEqual(classificar_risco(validade, hoje), esperado)

    def test_respeita_limites_das_faixas(self) -> None:
        hoje = date(2026, 6, 30)
        casos = (
            (0, ClassificacaoRisco.VENCIDO),
            (1, ClassificacaoRisco.CRITICO),
            (7, ClassificacaoRisco.CRITICO),
            (8, ClassificacaoRisco.ATENCAO),
            (30, ClassificacaoRisco.ATENCAO),
            (31, ClassificacaoRisco.NORMAL),
        )

        for dias, esperado in casos:
            with self.subTest(dias=dias):
                self.assertEqual(
                    classificar_risco(hoje + timedelta(days=dias), hoje),
                    esperado,
                )


class LoteValidatorTests(SimpleTestCase):
    def test_valida_e_normaliza_lote(self) -> None:
        lote, errors = validar_lote(
            {
                "codigo_produto": " PROD-001 ",
                "nome_produto": "Leite",
                "lote": "L-01",
                "quantidade": 10,
                "data_validade": "2026-07-15",
                "local": "Deposito A",
            }
        )

        self.assertEqual(errors, {})
        self.assertIsNotNone(lote)
        self.assertEqual(lote.codigo_produto, "PROD-001")
        self.assertEqual(lote.data_validade, date(2026, 7, 15))

    def test_rejeita_campos_invalidos(self) -> None:
        lote, errors = validar_lote(
            {
                "codigo_produto": "",
                "quantidade": 0,
                "data_validade": "30/06/2026",
            }
        )

        self.assertIsNone(lote)
        self.assertIn("codigo_produto", errors)
        self.assertIn("nome_produto", errors)
        self.assertIn("lote", errors)
        self.assertIn("quantidade", errors)
        self.assertIn("data_validade", errors)
        self.assertIn("local", errors)


class MonitoramentoServiceTests(SimpleTestCase):
    def test_monitora_lote_valido(self) -> None:
        hoje = date(2026, 7, 1)
        resultado = monitorar_lote(
            {
                "codigo_produto": "PROD-001",
                "nome_produto": "Leite",
                "lote": "L-01",
                "quantidade": 10,
                "data_validade": "2026-07-06",
                "local": "Deposito A",
            },
            hoje=hoje,
        )

        self.assertTrue(resultado.valido)
        self.assertEqual(resultado.dias_restantes, 5)
        self.assertEqual(resultado.classificacao, ClassificacaoRisco.CRITICO)
        self.assertEqual(resultado.erros, {})

    def test_interrompe_monitoramento_quando_lote_e_invalido(self) -> None:
        resultado = monitorar_lote({"codigo_produto": "PROD-001"})

        self.assertFalse(resultado.valido)
        self.assertIsNone(resultado.dias_restantes)
        self.assertIsNone(resultado.classificacao)
        self.assertIn("data_validade", resultado.erros)


class AdaptadorConsultaERPTests(SimpleTestCase):
    def test_contrato_expoe_somente_consulta(self) -> None:
        metodos_publicos = {
            nome
            for nome in dir(AdaptadorConsultaERP)
            if not nome.startswith("_")
        }

        self.assertEqual(metodos_publicos, {"consultar_lotes"})


class BackendRouteTests(APISimpleTestCase):
    def test_health(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_valida_lote(self) -> None:
        validade = date.today() + timedelta(days=5)
        response = self.client.post(
            "/lotes/validar",
            {
                "codigo_produto": "PROD-001",
                "nome_produto": "Leite",
                "lote": "L-01",
                "quantidade": 10,
                "data_validade": validade.isoformat(),
                "local": "Deposito A",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "valido": True,
                "dias_restantes": 5,
                "classificacao": "CRITICO",
                "erros": {},
            },
        )

    def test_retorna_erros_para_lote_invalido(self) -> None:
        response = self.client.post(
            "/lotes/validar",
            {"codigo_produto": "PROD-001"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["valido"])
        self.assertIn("data_validade", response.json()["erros"])
