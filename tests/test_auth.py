from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

API_KEY = "atlas-mvp-2026"


class AuthTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username="operador",
            email="operador@atlas.com",
            password="senha-forte-123",
            is_staff=False,
        )

    def login(self, username: str = "operador", password: str = "senha-forte-123") -> dict:
        response = self.client.post(
            "/api/v1/auth/login",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    def autenticar_bearer(self, access: str) -> None:
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def test_login_e_publico_e_retorna_tokens(self) -> None:
        dados = self.login()

        self.assertIn("refresh", dados)
        self.assertIn("access", dados)
        self.assertEqual(dados["user"]["username"], "operador")
        self.assertEqual(dados["user"]["email"], "operador@atlas.com")

    def test_login_com_credenciais_invalidas_retorna_401(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            {"username": "operador", "password": "senha-errada"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json(), {"erro": "Credenciais invalidas."})

    def test_me_exige_autenticacao(self) -> None:
        response = self.client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["autenticado"], False)

    def test_me_retorna_usuario_autenticado_por_jwt(self) -> None:
        dados = self.login()
        self.autenticar_bearer(dados["access"])

        response = self.client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["tipo"], "usuario")
        self.assertEqual(response.json()["usuario"]["username"], "operador")

    def test_me_aceita_api_key_como_servico(self) -> None:
        self.client.credentials(HTTP_X_API_KEY=API_KEY)

        response = self.client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["tipo"], "api_key")

    def test_refresh_troca_access_token(self) -> None:
        dados = self.login()

        response = self.client.post(
            "/api/v1/auth/refresh",
            {"refresh": dados["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())

    def test_refresh_invalido_retorna_401(self) -> None:
        response = self.client.post(
            "/api/v1/auth/refresh",
            {"refresh": "token-invalido"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_revoga_refresh_e_bloqueia_uso_posterior(self) -> None:
        dados = self.login()

        response = self.client.post(
            "/api/v1/auth/logout",
            {"refresh": dados["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_response = self.client.post(
            "/api/v1/auth/refresh",
            {"refresh": dados["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_de_negocio_aceita_jwt_sem_api_key(self) -> None:
        dados = self.login()
        self.autenticar_bearer(dados["access"])

        response = self.client.get("/api/v1/lotes")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_endpoint_de_negocio_rejeita_token_falso(self) -> None:
        self.autenticar_bearer("access-invalido")

        response = self.client.get("/api/v1/lotes")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_respeita_rate_limit_por_ip(self) -> None:
        from django.core.cache import cache

        # IP isolado para nao contaminar os demais testes da suite.
        self.client.credentials(HTTP_X_FORWARDED_FOR="10.9.9.9")
        try:
            # O rate real de login e 10/min (settings). A decima primeira
            # tentativa no mesmo IP estoura o limite e responde 429.
            for _ in range(10):
                response = self.client.post(
                    "/api/v1/auth/login",
                    {"username": "operador", "password": "errada"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            response = self.client.post(
                "/api/v1/auth/login",
                {"username": "operador", "password": "errada"},
                format="json",
            )

            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        finally:
            cache.clear()

    def test_rotas_de_docs_continuam_publicas(self) -> None:
        self.assertEqual(self.client.get("/api/docs/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/schema/").status_code, status.HTTP_200_OK)
