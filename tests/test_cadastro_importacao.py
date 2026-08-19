import io
from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import AnaliseLote, ConexaoSistema, HistoricoLote
from src.services.segredos import descriptografar


class CadastroLoteAPITests(TestCase):
    API_KEY = "atlas-mvp-2026"

    def setUp(self) -> None:
        self.client = APIClient()

    def autenticar(self) -> None:
        self.client.credentials(HTTP_X_API_KEY=self.API_KEY)

    def payload_valido(self) -> dict:
        validade = (date.today() + timedelta(days=5)).isoformat()
        return {
            "nome_produto": "Leite integral",
            "codigo_produto": "MAN-001",
            "lote": "L-MAN-2026-01",
            "quantidade_inicial": "12.500",
            "data_validade": validade,
            "local": "Camara fria A",
            "unidade": "1L",
            "origem": "MANUAL",
        }

    def test_cadastrar_exige_api_key(self) -> None:
        response = self.client.post(
            "/api/v1/lotes/cadastrar",
            self.payload_valido(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_conexao_sistema_salva_urls_criptografadas_e_retorna_mascarado(self) -> None:
        self.autenticar()

        response = self.client.post(
            "/api/v1/config/conexoes-sistema",
            {
                "nome_sistema": "Bling",
                "api_url": "https://bling.example/api/sensivel",
                "webhook_url": "https://bling.example/webhook/sensivel",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertTrue(payload["api_url_configurada"])
        self.assertTrue(payload["webhook_url_configurada"])
        self.assertNotIn("sensivel", payload["api_url_mascarada"])
        self.assertNotIn("sensivel", payload["webhook_url_mascarada"])
        self.assertEqual(payload["api_url_mascarada"], "https://bling.example/***")

        conexao = ConexaoSistema.objects.get(id=payload["id"])
        self.assertNotIn("bling.example", conexao.api_url_encrypted)
        self.assertEqual(descriptografar(conexao.api_url_encrypted), "https://bling.example/api/sensivel")

        get_response = self.client.get("/api/v1/config/conexoes-sistema")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertNotIn("https://bling.example/api/sensivel", str(get_response.json()))

    def test_conexao_sistema_exige_https(self) -> None:
        self.autenticar()

        response = self.client.post(
            "/api/v1/config/conexoes-sistema",
            {"nome_sistema": "Bling", "api_url": "http://bling.example/api"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conexao_sistema_limita_a_tres_conexoes(self) -> None:
        self.autenticar()

        for indice in range(ConexaoSistema.MAX_CONEXOES):
            response = self.client.post(
                "/api/v1/config/conexoes-sistema",
                {"nome_sistema": f"Sistema {indice}"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            "/api/v1/config/conexoes-sistema",
            {"nome_sistema": "Sistema extra"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ConexaoSistema.objects.count(), ConexaoSistema.MAX_CONEXOES)

    def test_conexao_sistema_patch_parcial_nao_apaga_segredo_existente(self) -> None:
        self.autenticar()
        criada = self.client.post(
            "/api/v1/config/conexoes-sistema",
            {"nome_sistema": "Bling", "api_url": "https://bling.example/api"},
            format="json",
        ).json()

        response = self.client.patch(
            f"/api/v1/config/conexoes-sistema/{criada['id']}",
            {"nome_sistema": "Bling Renomeado"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["nome_sistema"], "Bling Renomeado")
        self.assertTrue(payload["api_url_configurada"])

        conexao = ConexaoSistema.objects.get(id=criada["id"])
        self.assertEqual(descriptografar(conexao.api_url_encrypted), "https://bling.example/api")

    def test_conexao_sistema_delete_libera_uma_vaga(self) -> None:
        self.autenticar()
        criada = self.client.post(
            "/api/v1/config/conexoes-sistema",
            {"nome_sistema": "Bling"},
            format="json",
        ).json()

        response = self.client.delete(f"/api/v1/config/conexoes-sistema/{criada['id']}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ConexaoSistema.objects.count(), 0)

    def test_cadastrar_cria_analise_e_classifica_no_servidor(self) -> None:
        self.autenticar()

        response = self.client.post(
            "/api/v1/lotes/cadastrar",
            self.payload_valido(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        analise = AnaliseLote.objects.get(
            codigo_produto="MAN-001",
            lote="L-MAN-2026-01",
        )
        self.assertEqual(response.json()["id"], analise.id)
        self.assertEqual(analise.classificacao, "CRITICO")
        self.assertEqual(analise.origem, "MANUAL")
        self.assertEqual(analise.nome_produto, "Leite integral")
        self.assertEqual(str(analise.quantidade_inicial), "12.500")
        self.assertEqual(str(analise.quantidade_atual), "12.500")
        self.assertEqual(analise.local, "Camara fria A")
        self.assertEqual(analise.unidade, "1L")

    def test_cadastrar_atualiza_analise_existente(self) -> None:
        self.autenticar()
        primeiro = self.client.post(
            "/api/v1/lotes/cadastrar",
            self.payload_valido(),
            format="json",
        )
        self.assertEqual(primeiro.status_code, status.HTTP_201_CREATED)

        resposta_atualizacao = self.client.post(
            "/api/v1/lotes/cadastrar",
            {
                **self.payload_valido(),
                "data_validade": (date.today() + timedelta(days=60)).isoformat(),
                "quantidade_inicial": "8.000",
                "local": "Prateleira B",
            },
            format="json",
        )

        self.assertEqual(
            resposta_atualizacao.status_code,
            status.HTTP_200_OK,
        )
        analise = AnaliseLote.objects.get(
            codigo_produto="MAN-001",
            lote="L-MAN-2026-01",
        )
        self.assertEqual(analise.classificacao, "NORMAL")
        self.assertEqual(str(analise.quantidade_atual), "8.000")
        self.assertEqual(analise.local, "Prateleira B")
        self.assertEqual(HistoricoLote.objects.count(), 1)

    def test_atualizar_lote_reduz_quantidade_e_registra_historico(self) -> None:
        self.autenticar()
        criado = self.client.post("/api/v1/lotes/cadastrar", self.payload_valido(), format="json")
        lote_id = criado.json()["id"]

        response = self.client.patch(
            f"/api/v1/lotes/{lote_id}/editar",
            {"quantidade_atual": "7.000", "local": "Camara fria B"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        analise = AnaliseLote.objects.get(id=lote_id)
        self.assertEqual(str(analise.quantidade_atual), "7.000")
        self.assertEqual(analise.local, "Camara fria B")
        historico = HistoricoLote.objects.get(analise_lote=analise)
        self.assertEqual(str(historico.quantidade_anterior), "12.500")
        self.assertEqual(str(historico.quantidade_nova), "7.000")
        self.assertEqual(historico.local_anterior, "Camara fria A")
        self.assertEqual(historico.local_novo, "Camara fria B")

    def test_atualizar_lote_rejeita_aumento_manual(self) -> None:
        self.autenticar()
        criado = self.client.post("/api/v1/lotes/cadastrar", self.payload_valido(), format="json")

        response = self.client.patch(
            f"/api/v1/lotes/{criado.json()['id']}/editar",
            {"quantidade_atual": "13.000"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_historico_alteracoes(self) -> None:
        self.autenticar()
        criado = self.client.post("/api/v1/lotes/cadastrar", self.payload_valido(), format="json")
        self.client.patch(
            f"/api/v1/lotes/{criado.json()['id']}/editar",
            {"quantidade_atual": "2.000", "local": "Balcao"},
            format="json",
        )

        response = self.client.get("/api/v1/historico-alteracoes")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        descricoes = {item["descricao"] for item in response.json()}
        self.assertTrue(any("L-MAN-2026-01" in descricao for descricao in descricoes))

    def test_cadastrar_payload_invalido_retorna_400(self) -> None:
        self.autenticar()

        response = self.client.post(
            "/api/v1/lotes/cadastrar",
            {"lote": "L-SEM-CODIGO"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detalhes", response.json())

    def test_cadastrar_usa_origem_padrao_quando_ausente(self) -> None:
        self.autenticar()
        payload = self.payload_valido()
        del payload["origem"]

        response = self.client.post(
            "/api/v1/lotes/cadastrar",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        analise = AnaliseLote.objects.get(
            codigo_produto="MAN-001",
            lote="L-MAN-2026-01",
        )
        self.assertEqual(analise.origem, "MANUAL")


class ImportacaoLoteAPITests(TestCase):
    API_KEY = "atlas-mvp-2026"

    def setUp(self) -> None:
        self.client = APIClient()

    def autenticar(self) -> None:
        self.client.credentials(HTTP_X_API_KEY=self.API_KEY)

    def test_importar_exige_api_key(self) -> None:
        arquivo = SimpleUploadedFile(
            "lotes.csv",
            b"codigo_produto,lote,quantidade_inicial,data_validade\n",
            content_type="text/csv",
        )
        response = self.client.post(
            "/api/v1/lotes/importar",
            {"arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_importar_csv_valido_importa_lotes(self) -> None:
        self.autenticar()
        validade = (date.today() + timedelta(days=10)).isoformat()
        conteudo = (
            "codigo_produto,lote,quantidade_inicial,data_validade,origem\n"
            f"IMP-001,L-IMP-01,10,{validade},CSV\n"
            f"IMP-002,L-IMP-02,20,{validade},CSV\n"
        ).encode("utf-8")
        arquivo = SimpleUploadedFile(
            "lotes.csv",
            conteudo,
            content_type="text/csv",
        )

        response = self.client.post(
            "/api/v1/lotes/importar",
            {"arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        corpo = response.json()
        self.assertEqual(corpo["total"], 2)
        self.assertEqual(corpo["importados"], 2)
        self.assertEqual(corpo["atualizados"], 0)
        self.assertEqual(corpo["invalidos"], 0)
        self.assertEqual(corpo["erros"], [])
        self.assertEqual(AnaliseLote.objects.count(), 2)

    def test_importar_csv_coleta_erros_por_linha(self) -> None:
        self.autenticar()
        validade = (date.today() + timedelta(days=5)).isoformat()
        conteudo = (
            "codigo_produto,lote,quantidade_inicial,data_validade\n"
            f"IMP-BOM,L-BOM,5,{validade}\n"
            "IMP-RUIM,L-RUIM,2,31/13/2099\n"
            ",L-SEM-CODIGO,1,2026-01-01\n"
        ).encode("utf-8")
        arquivo = SimpleUploadedFile(
            "lotes.csv",
            conteudo,
            content_type="text/csv",
        )

        response = self.client.post(
            "/api/v1/lotes/importar",
            {"arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        corpo = response.json()
        self.assertEqual(corpo["total"], 3)
        self.assertEqual(corpo["importados"], 1)
        self.assertEqual(corpo["invalidos"], 2)
        self.assertEqual(len(corpo["erros"]), 2)
        self.assertEqual(corpo["erros"][0]["linha"], 2)
        self.assertEqual(AnaliseLote.objects.count(), 1)

    def test_importar_rejeita_extensao_nao_suportada(self) -> None:
        self.autenticar()
        arquivo = SimpleUploadedFile(
            "lotes.xls",
            b"\xd0\xcf\x11\xe0",
            content_type="application/vnd.ms-excel",
        )

        response = self.client.post(
            "/api/v1/lotes/importar",
            {"arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nao suportado", response.json()["erro"])

    def test_importar_sem_arquivo_retorna_400(self) -> None:
        self.autenticar()

        response = self.client.post(
            "/api/v1/lotes/importar",
            {},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_importar_json_valido_importa_lotes(self) -> None:
        self.autenticar()
        validade = (date.today() + timedelta(days=40)).isoformat()
        conteudo = (
            '{"lotes": ['
            '  {"codigo_produto": "J-001", "lote": "LJ-01", "quantidade": 3, "data_validade": "' + validade + '"},'
            '  {"codigo": "J-002", "lote": "LJ-02", "qtd": 4, "vencimento": "' + validade + '"}'
            "]}"
        ).encode("utf-8")
        arquivo = SimpleUploadedFile(
            "lotes.json",
            conteudo,
            content_type="application/json",
        )

        response = self.client.post(
            "/api/v1/lotes/importar",
            {"arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["importados"], 2)
        self.assertEqual(AnaliseLote.objects.count(), 2)

    def test_importar_xlsx_valido_importa_lotes(self) -> None:
        from openpyxl import Workbook

        self.autenticar()
        validade = (date.today() + timedelta(days=15)).isoformat()
        workbook = Workbook()
        planilha = workbook.active
        planilha.append(["codigo_produto", "lote", "quantidade", "data_validade"])
        planilha.append(["XLSX-001", "LX-01", 1, validade])
        planilha.append(["XLSX-002", "LX-02", 2, validade])
        buffer = io.BytesIO()
        workbook.save(buffer)
        arquivo = SimpleUploadedFile(
            "lotes.xlsx",
            buffer.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )

        response = self.client.post(
            "/api/v1/lotes/importar",
            {"arquivo": arquivo},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["importados"], 2)
        self.assertEqual(AnaliseLote.objects.count(), 2)


class ConfigSistemaAPITests(TestCase):
    API_KEY = "atlas-mvp-2026"

    def setUp(self) -> None:
        self.client = APIClient()

    def test_config_exige_api_key(self) -> None:
        response = self.client.get("/api/v1/config")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_config_retorna_limites_do_servidor(self) -> None:
        self.client.credentials(HTTP_X_API_KEY=self.API_KEY)

        response = self.client.get("/api/v1/config")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        corpo = response.json()
        self.assertEqual(corpo["dias_critico"], 7)
        self.assertEqual(corpo["dias_atencao"], 30)
        self.assertTrue(corpo["api_key_requerida"])
        self.assertIn("CRITICO", corpo["classificacao_descricao"])
