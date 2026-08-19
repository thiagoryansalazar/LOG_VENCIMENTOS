import base64
import hashlib
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.ATLAS_SECRETS_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def criptografar(valor: str) -> str:
    if not valor:
        return ""
    return _fernet().encrypt(valor.encode("utf-8")).decode("utf-8")


def descriptografar(valor: str) -> str:
    if not valor:
        return ""
    return _fernet().decrypt(valor.encode("utf-8")).decode("utf-8")


def mascarar_url(valor: str) -> str:
    """Mascara um endereco sensivel de conexao do cliente.

    So mostra esquema e dominio. Path, query string e fragmento nunca sao
    expostos -- mesmo parcialmente -- porque e comum tokens/chaves de acesso
    virem embutidos ali (ex.: `?api_key=...` ou `/token/<segredo>`).
    """
    if not valor:
        return ""
    partes = urlsplit(valor)
    if not partes.scheme or not partes.netloc:
        return "configurado"
    return f"{partes.scheme}://{partes.netloc}/***"
