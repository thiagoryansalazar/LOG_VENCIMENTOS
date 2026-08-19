from django.test import TestCase
from rest_framework.test import APIClient


class SecurityHeadersTests(TestCase):
    """Garante que a SPA e servida com os cabecalhos que contem XSS e clickjacking.

    Os tokens JWT ficam em localStorage, legivel por qualquer script da origem.
    A CSP e o que impede um payload injetado de executar e roubar a sessao, por
    isso as diretivas criticas sao travadas por teste.
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_health_responde_com_content_security_policy(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Content-Security-Policy", response)

    def test_csp_bloqueia_script_externo_e_inline(self) -> None:
        response = self.client.get("/health")
        politica = response["Content-Security-Policy"]

        self.assertIn("script-src 'self'", politica)
        # Sao justamente estas duas permissoes que fariam um XSS injetado
        # executar; a politica nao pode reintroduzi-las em script-src.
        self.assertNotIn("script-src 'self' 'unsafe-inline'", politica)
        self.assertNotIn("unsafe-eval", politica)
        self.assertIn("object-src 'none'", politica)
        self.assertIn("base-uri 'self'", politica)

    def test_bloqueia_embutir_o_app_em_iframe_de_terceiros(self) -> None:
        response = self.client.get("/health")

        self.assertIn("frame-ancestors 'none'", response["Content-Security-Policy"])
        self.assertEqual(response["X-Frame-Options"], "DENY")

    def test_documentacao_openapi_fica_fora_da_csp(self) -> None:
        """A UI do Swagger depende de script inline proprio e quebraria com a CSP."""
        response = self.client.get("/api/docs/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Content-Security-Policy", response)

    def test_nosniff_e_referrer_policy_presentes(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "same-origin")
