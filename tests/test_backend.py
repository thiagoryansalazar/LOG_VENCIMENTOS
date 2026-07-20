from datetime import date, timedelta
import math

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APISimpleTestCase

from core.models import Alerta, AnaliseLote
from src.integrations import (
    AdaptadorCSV,
    AdaptadorConsultaERP,
    AdaptadorFonteExterna,
    MapeadorCSV,
    MapeadorCampos,
    ModoIntegracao,
)
from src.services import (
    ClassificacaoRisco,
    EmailSenderInterface,
    calcular_dias_restantes,
    classificar_risco,
    disparar_alerta,
    monitorar_lote,
)
from src.services.email import InMemoryRateLimiter
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

    def test_hoje_e_obrigatorio_no_core(self) -> None:
        validade = date(2026, 7, 1)

        with self.assertRaises(TypeError):
            calcular_dias_restantes(validade)

        with self.assertRaises(TypeError):
            classificar_risco(validade)

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

    def test_rejeita_quantidade_ausente_booleano_nao_numerica_e_infinita(self) -> None:
        payload_base = {
            "codigo_produto": "PROD-001",
            "nome_produto": "Leite",
            "lote": "L-01",
            "data_validade": "2026-07-15",
            "local": "Deposito A",
        }
        casos = (
            ({}, "Este campo e obrigatorio."),
            ({"quantidade": True}, "Valor booleano nao e aceito como quantidade."),
            ({"quantidade": "dez"}, "Deve ser um valor numerico."),
            ({"quantidade": math.inf}, "Deve ser um numero finito."),
            ({"quantidade": math.nan}, "Deve ser um numero finito."),
            ({"quantidade": 0}, "Deve ser maior que zero."),
        )

        for extra, mensagem in casos:
            with self.subTest(extra=extra):
                lote, errors = validar_lote(payload_base | extra)

                self.assertIsNone(lote)
                self.assertEqual(errors["quantidade"], [mensagem])

    def test_limita_campos_de_texto_a_255_caracteres(self) -> None:
        payload = {
            "codigo_produto": "P" * 256,
            "nome_produto": "Leite",
            "lote": "L-01",
            "quantidade": 10,
            "data_validade": "2026-07-15",
            "local": "Deposito A",
        }

        lote, errors = validar_lote(payload)

        self.assertIsNone(lote)
        self.assertEqual(
            errors["codigo_produto"],
            ["Este campo deve ter no maximo 255 caracteres."],
        )


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
        resultado = monitorar_lote(
            {"codigo_produto": "PROD-001"},
            hoje=date(2026, 7, 1),
        )

        self.assertFalse(resultado.valido)
        self.assertIsNone(resultado.dias_restantes)
        self.assertIsNone(resultado.classificacao)
        self.assertIn("data_validade", resultado.erros)


class FakeEmailSender(EmailSenderInterface):
    def __init__(self) -> None:
        self.envios: list[tuple[str, str, str]] = []

    def enviar(self, destinatario: str, assunto: str, corpo: str) -> None:
        self.envios.append((destinatario, assunto, corpo))


class AlertaServiceTests(TestCase):
    def criar_analise(self, lote: str = "L2026-01") -> AnaliseLote:
        return AnaliseLote.objects.create(
            codigo_produto="PROD-001",
            lote=lote,
            data_validade=date(2026, 7, 20),
            dias_restantes=3,
            classificacao="CRITICO",
            origem="CSV",
        )

    def test_dispara_alerta_e_cria_registro(self) -> None:
        sender = FakeEmailSender()
        analise = self.criar_analise()

        resultado = disparar_alerta(
            analise,
            "CRITICO",
            "gestor@empresa.com",
            email_sender=sender,
        )

        self.assertTrue(resultado.enviado)
        self.assertFalse(resultado.suprimido)
        self.assertEqual(len(sender.envios), 1)
        self.assertEqual(Alerta.objects.count(), 1)
        alerta = Alerta.objects.get()
        self.assertIsNotNone(alerta.enviado_em)
        self.assertEqual(alerta.destinatario, "gestor@empresa.com")

    def test_suprime_alerta_duplicado_em_24_horas(self) -> None:
        sender = FakeEmailSender()
        analise = self.criar_analise()

        primeiro = disparar_alerta(
            analise,
            "CRITICO",
            "gestor@empresa.com",
            email_sender=sender,
        )
        segundo = disparar_alerta(
            analise,
            "CRITICO",
            "gestor@empresa.com",
            email_sender=sender,
        )

        self.assertTrue(primeiro.enviado)
        self.assertTrue(segundo.suprimido)
        self.assertEqual(segundo.motivo, "alerta suprimido por duplicidade em 24h")
        self.assertEqual(len(sender.envios), 1)
        self.assertEqual(Alerta.objects.count(), 1)

    def test_alerta_antigo_nao_bloqueia_novo_envio(self) -> None:
        sender = FakeEmailSender()
        analise = self.criar_analise()
        Alerta.objects.create(
            analise_lote=analise,
            classificacao="CRITICO",
            mensagem="alerta antigo",
            destinatario="gestor@empresa.com",
            enviado_em=timezone.now() - timezone.timedelta(hours=25),
        )

        resultado = disparar_alerta(
            analise,
            "CRITICO",
            "gestor@empresa.com",
            email_sender=sender,
        )

        self.assertTrue(resultado.enviado)
        self.assertEqual(len(sender.envios), 1)
        self.assertEqual(Alerta.objects.count(), 2)

    def test_rate_limit_suprime_envio_excedente(self) -> None:
        sender = FakeEmailSender()
        rate_limiter = InMemoryRateLimiter(limite_por_minuto=1)
        primeira_analise = self.criar_analise("L2026-01")
        segunda_analise = self.criar_analise("L2026-02")

        primeiro = disparar_alerta(
            primeira_analise,
            "CRITICO",
            "gestor@empresa.com",
            email_sender=sender,
            rate_limiter=rate_limiter,
        )
        segundo = disparar_alerta(
            segunda_analise,
            "CRITICO",
            "gestor@empresa.com",
            email_sender=sender,
            rate_limiter=rate_limiter,
        )

        self.assertTrue(primeiro.enviado)
        self.assertTrue(segundo.suprimido)
        self.assertEqual(segundo.motivo, "rate limit de email excedido")
        self.assertEqual(len(sender.envios), 1)
        self.assertEqual(Alerta.objects.count(), 1)

    def test_monitoramento_dispara_alerta_quando_recebe_analise_persistida(self) -> None:
        sender = FakeEmailSender()
        analise = self.criar_analise()

        resultado = monitorar_lote(
            {
                "codigo_produto": "PROD-001",
                "nome_produto": "Leite",
                "lote": "L2026-01",
                "quantidade": 10,
                "data_validade": "2026-07-20",
                "local": "Deposito A",
            },
            hoje=date(2026, 7, 17),
            analise_lote=analise,
            destinatario_alerta="gestor@empresa.com",
            email_sender=sender,
        )

        self.assertTrue(resultado.valido)
        self.assertIsNotNone(resultado.alerta)
        assert resultado.alerta is not None
        self.assertTrue(resultado.alerta.enviado)
        self.assertEqual(len(sender.envios), 1)
        self.assertEqual(Alerta.objects.count(), 1)


class AdaptadorConsultaERPTests(SimpleTestCase):
    class AdaptadorFake(AdaptadorConsultaERP):
        def consultar_lotes(self):
            return [{"lote": "L-01"}]

    def test_adaptador_generico_delega_para_consulta_erp(self) -> None:
        adaptador = self.AdaptadorFake()

        self.assertEqual(
            list(adaptador.obter_registros({"id": "L-01"})),
            [{"lote": "L-01"}],
        )

    def test_adaptador_nao_expoe_operacao_de_escrita(self) -> None:
        metodos_publicos = {
            nome for nome in dir(AdaptadorConsultaERP) if not nome.startswith("_")
        }

        self.assertNotIn("salvar", metodos_publicos)
        self.assertNotIn("atualizar", metodos_publicos)


class IntegracaoExternaTests(SimpleTestCase):
    def test_expoe_os_tres_modos_definidos(self) -> None:
        self.assertEqual(
            {modo.value for modo in ModoIntegracao},
            {"EVENTO", "CONSULTA_AGENDADA", "ARQUIVO"},
        )

    def test_adaptador_base_exige_leitura(self) -> None:
        self.assertIn(
            "obter_registros",
            AdaptadorFonteExterna.__abstractmethods__,
        )

    def test_mapeador_exige_traducao_de_campos(self) -> None:
        self.assertIn("mapear", MapeadorCampos.__abstractmethods__)


class IntegracaoCSVTests(SimpleTestCase):
    def test_adaptador_csv_le_arquivo_mockado(self) -> None:
        registros = list(AdaptadorCSV("lotes_mockados.csv").obter_registros())

        self.assertEqual(len(registros), 6)
        self.assertEqual(registros[0]["codigo_produto"], "PROD-001")

    def test_mapeador_csv_converte_campos(self) -> None:
        registro = {
            "codigo_produto": " PROD-001 ",
            "nome_produto": "Leite Integral",
            "lote": "L2026-001",
            "quantidade": "120",
            "data_validade": "2026-07-20",
            "local": "CD Sao Paulo",
        }

        payload = MapeadorCSV().mapear(registro)

        self.assertEqual(payload["codigo_produto"], "PROD-001")
        self.assertEqual(payload["quantidade"], 120)
        self.assertEqual(payload["data_validade"], date(2026, 7, 20))

    def test_fluxo_csv_cobre_classificacoes_esperadas(self) -> None:
        adaptador = AdaptadorCSV("lotes_mockados.csv")
        mapeador = MapeadorCSV()
        hoje = date(2026, 7, 17)
        classificacoes: dict[str, int] = {}

        for registro in adaptador.obter_registros():
            payload = mapeador.mapear(registro)
            resultado = monitorar_lote(payload, hoje=hoje)
            assert resultado.classificacao is not None
            classificacoes[resultado.classificacao.value] = (
                classificacoes.get(resultado.classificacao.value, 0) + 1
            )

        self.assertEqual(
            classificacoes,
            {
                "VENCIDO": 2,
                "CRITICO": 2,
                "ATENCAO": 1,
                "NORMAL": 1,
            },
        )


class BackendRouteTests(APISimpleTestCase):
    API_KEY = "atlas-mvp-2026"

    def test_health(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_rejeita_rota_protegida_sem_api_key(self) -> None:
        response = self.client.post("/lotes/validar", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"erro": "API Key ausente ou invalida."})

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
            HTTP_X_API_KEY=self.API_KEY,
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
            HTTP_X_API_KEY=self.API_KEY,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.json()["valido"])
        self.assertIn("data_validade", response.json()["erros"])
