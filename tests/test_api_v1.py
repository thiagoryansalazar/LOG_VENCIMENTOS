from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import AnaliseLote
from src.services.alerta import ResultadoAlerta


class APIV1Tests(TestCase):
    API_KEY = "atlas-mvp-2026"

    def setUp(self) -> None:
        self.client = APIClient()
        self.analise_critica = AnaliseLote.objects.create(
            codigo_produto="PROD-001",
            lote="L2026-001",
            data_validade=date(2026, 7, 20),
            dias_restantes=3,
            classificacao="CRITICO",
            origem="CSV",
        )
        self.analise_vencida = AnaliseLote.objects.create(
            codigo_produto="PROD-002",
            lote="L2026-002",
            data_validade=date(2026, 7, 10),
            dias_restantes=-7,
            classificacao="VENCIDO",
            origem="CSV",
        )
        self.analise_normal = AnaliseLote.objects.create(
            codigo_produto="PROD-003",
            lote="L2026-003",
            data_validade=date(2026, 9, 1),
            dias_restantes=45,
            classificacao="NORMAL",
            origem="CSV",
        )

    def autenticar(self) -> None:
        self.client.credentials(HTTP_X_API_KEY=self.API_KEY)

    def test_docs_e_schema_sao_publicos(self) -> None:
        docs_response = self.client.get("/api/docs/")
        schema_response = self.client.get("/api/schema/")

        self.assertEqual(docs_response.status_code, status.HTTP_200_OK)
        self.assertEqual(schema_response.status_code, status.HTTP_200_OK)

    def test_lotes_exige_api_key(self) -> None:
        response = self.client.get("/api/v1/lotes")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"erro": "API Key ausente ou invalida."})

    def test_preflight_cors_nao_exige_api_key(self) -> None:
        """O navegador nao envia X-API-Key no preflight OPTIONS.

        Exigir a chave aqui derruba todo consumo da SPA antes da requisicao
        real acontecer, com um 401 que o curl nunca reproduz.
        """
        response = self.client.options(
            "/api/v1/lotes",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-api-key",
        )

        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:5173",
        )

    def test_resposta_autenticada_traz_header_cors(self) -> None:
        self.autenticar()

        response = self.client.get(
            "/api/v1/lotes",
            HTTP_ORIGIN="http://localhost:5173",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:5173",
        )

    def test_origem_nao_autorizada_nao_recebe_header_cors(self) -> None:
        self.autenticar()

        response = self.client.get(
            "/api/v1/lotes",
            HTTP_ORIGIN="http://origem-nao-autorizada.example",
        )

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_lista_lotes_com_api_key(self) -> None:
        self.autenticar()

        response = self.client.get("/api/v1/lotes")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)

    def test_lista_lotes_com_filtros(self) -> None:
        self.autenticar()

        response = self.client.get(
            "/api/v1/lotes",
            {"codigo_produto": "PROD-001", "lote": "L2026-001"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["codigo_produto"], "PROD-001")

    def test_lista_lotes_criticos_e_vencidos(self) -> None:
        self.autenticar()

        response = self.client.get("/api/v1/lotes/criticos")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        classificacoes = {item["classificacao"] for item in response.json()}
        self.assertEqual(classificacoes, {"CRITICO", "VENCIDO"})
        self.assertNotIn(
            self.analise_normal.id,
            {item["id"] for item in response.json()},
        )

    def test_disparar_alerta_exige_api_key(self) -> None:
        response = self.client.post(
            "/api/v1/alertas/disparar",
            {
                "analise_lote_id": self.analise_critica.id,
                "destinatario": "gestor@empresa.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_disparar_alerta_retorna_404_para_analise_inexistente(self) -> None:
        self.autenticar()

        response = self.client.post(
            "/api/v1/alertas/disparar",
            {"analise_lote_id": 9999, "destinatario": "gestor@empresa.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json(),
            {"erro": "AnaliseLote nao encontrado.", "detalhes": {}},
        )

    @patch("src.routes.views.disparar_alerta")
    def test_disparar_alerta_manual_chama_servico(self, mock_disparar) -> None:
        self.autenticar()
        mock_disparar.return_value = ResultadoAlerta(
            enviado=True,
            suprimido=False,
            motivo="alerta enviado",
            alerta_id=123,
        )

        response = self.client.post(
            "/api/v1/alertas/disparar",
            {
                "analise_lote_id": self.analise_critica.id,
                "destinatario": "gestor@empresa.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "enviado": True,
                "suprimido": False,
                "motivo": "alerta enviado",
                "alerta_id": 123,
            },
        )
        mock_disparar.assert_called_once_with(
            analise_lote=self.analise_critica,
            classificacao="CRITICO",
            destinatario="gestor@empresa.com",
        )

    def test_consultar_lote_por_id_exige_api_key(self) -> None:
        response = self.client.get(f"/api/v1/lotes/{self.analise_critica.id}")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_consultar_lote_por_id_retorna_analise(self) -> None:
        self.autenticar()

        response = self.client.get(f"/api/v1/lotes/{self.analise_critica.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], self.analise_critica.id)
        self.assertEqual(response.json()["codigo_produto"], "PROD-001")
        self.assertEqual(response.json()["classificacao"], "CRITICO")

    def test_consultar_lote_por_id_retorna_404_para_id_inexistente(self) -> None:
        self.autenticar()

        response = self.client.get("/api/v1/lotes/9999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json(),
            {"erro": "AnaliseLote nao encontrado.", "detalhes": {}},
        )

    def test_api_v1_valida_lote(self) -> None:
        self.autenticar()
        validade = date.today() + timedelta(days=5)

        response = self.client.post(
            "/api/v1/lotes/validar",
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
        self.assertEqual(response.json()["classificacao"], "CRITICO")
