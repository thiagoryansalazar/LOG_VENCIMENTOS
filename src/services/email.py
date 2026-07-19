from __future__ import annotations

import smtplib
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from email.message import EmailMessage
from threading import Lock

from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string


class EmailSenderInterface(ABC):
    @abstractmethod
    def enviar(self, destinatario: str, assunto: str, corpo: str) -> None:
        """Envia um email para o destinatario informado."""


class GmailSender(EmailSenderInterface):
    def enviar(self, destinatario: str, assunto: str, corpo: str) -> None:
        usuario = settings.EMAIL_HOST_USER
        senha = settings.EMAIL_HOST_PASSWORD

        if not usuario or not senha:
            raise RuntimeError(
                "Credenciais de email ausentes. Configure EMAIL_HOST_USER e "
                "EMAIL_HOST_PASSWORD no .env."
            )

        mensagem = EmailMessage()
        mensagem["From"] = usuario
        mensagem["To"] = destinatario
        mensagem["Subject"] = assunto
        mensagem.set_content(corpo)

        with smtplib.SMTP(
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
            timeout=settings.EMAIL_TIMEOUT,
        ) as smtp:
            if settings.EMAIL_USE_TLS:
                smtp.starttls()
            smtp.login(usuario, senha)
            smtp.send_message(mensagem)


class RateLimitExceeded(RuntimeError):
    pass


@dataclass(slots=True)
class InMemoryRateLimiter:
    limite_por_minuto: int
    _envios: deque = field(default_factory=deque)
    _lock: Lock = field(default_factory=Lock)

    def permitir(self) -> bool:
        agora = timezone.now()
        janela_inicio = agora - timezone.timedelta(minutes=1)

        with self._lock:
            while self._envios and self._envios[0] < janela_inicio:
                self._envios.popleft()

            if len(self._envios) >= self.limite_por_minuto:
                return False

            self._envios.append(agora)
            return True


def carregar_email_sender() -> EmailSenderInterface:
    classe_sender = import_string(settings.EMAIL_SENDER_CLASS)
    sender = classe_sender()

    if not isinstance(sender, EmailSenderInterface):
        raise TypeError(
            f"{settings.EMAIL_SENDER_CLASS} deve implementar EmailSenderInterface."
        )

    return sender


email_rate_limiter = InMemoryRateLimiter(settings.EMAIL_RATE_LIMIT_PER_MINUTE)
