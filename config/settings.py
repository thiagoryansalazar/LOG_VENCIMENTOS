import logging
import os
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-development-key")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "core.apps.CoreConfig",
    "src.apps.LogVencimentosConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # CorsMiddleware precisa vir antes de CommonMiddleware e do middleware de
    # API Key: ele responde ao preflight OPTIONS por conta propria, sem deixar
    # a requisicao seguir para a checagem de chave.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "src.config.middleware.SecurityHeadersMiddleware",
    "src.config.middleware.AtlasAPIKeyMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
PROJECT_NAME = "ATLAS Vencimentos"

DATABASES = {"default": env.db()}
ATLAS_API_KEY = env("ATLAS_API_KEY")
EMAIL_SENDER_CLASS = env(
    "EMAIL_SENDER_CLASS",
    default="src.services.email.GmailSender",
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=30)
EMAIL_RATE_LIMIT_PER_MINUTE = env.int("EMAIL_RATE_LIMIT_PER_MINUTE", default=5)
DIAS_CRITICO = env.int("DIAS_CRITICO", default=7)
DIAS_ATENCAO = env.int("DIAS_ATENCAO", default=30)
ATLAS_GESTOR_NOME = env("ATLAS_GESTOR_NOME", default="Gestor ATLAS")
ATLAS_EMPRESA_NOME = env("ATLAS_EMPRESA_NOME", default="Empresa ATLAS")

# Chave dedicada para criptografar dados sensiveis do cliente (conexoes de
# sistema/ERP). Separada do SECRET_KEY do Django de proposito: SECRET_KEY
# tem outros usos (sessions, tokens CSRF) e girar/expor ela nao deveria nunca
# ficar acoplado a segredos de conexao de cliente. Fora de DEBUG e obrigatoria.
ATLAS_SECRETS_KEY = env("ATLAS_SECRETS_KEY", default="")
if not ATLAS_SECRETS_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "ATLAS_SECRETS_KEY e obrigatoria fora de DEBUG: sem ela, dados sensiveis "
            "de conexao do cliente ficariam dependentes do SECRET_KEY do Django."
        )
    ATLAS_SECRETS_KEY = SECRET_KEY

# Autenticacao por JWT (djangorestframework-simplejwt).
# O access token tem vida curta e e trocado pelo refresh token; o refresh tem
# vida maior e pode ser invalidado (blacklist) no logout.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "ALGORITHM": "HS256",
}

# Camada de transporte (RNF). Por padrao desligada no MVP local; em producao,
# ative via env com TLS terminado no proxy/infra.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)

# CORS. Em desenvolvimento a SPA roda em outra origem (Vite em :5173) e
# autentica por Bearer JWT. As origens permitidas sao configuraveis por
# ambiente: o default cobre apenas o desenvolvimento local e nao deve ser
# reaproveitado em producao.
CORS_ALLOWED_ORIGINS = [
    origem.strip()
    for origem in env(
        "CORS_ALLOWED_ORIGINS",
        default="http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origem.strip()
]
# `x-api-key` foi deliberadamente removido desta lista. A chave de servico e
# uma credencial de integracao servidor-a-servidor e nunca deve trafegar a
# partir de um navegador -- de dentro do browser ela ficaria visivel no bundle
# e em toda requisicao da aba Network. Sem o header liberado aqui, o preflight
# barra qualquer tentativa de reintroduzir esse envio pelo frontend.
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
FRONTEND_DIST_DIR = Path(
    env("FRONTEND_DIST_DIR", default=str(BASE_DIR.parent / "ATLAS - FRONT_END" / "dist"))
)
STATICFILES_DIRS = [FRONTEND_DIST_DIR] if FRONTEND_DIST_DIR.exists() else []
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        # Rate limit dedicado ao login (RNF anti brute-force): por IP, por minuto.
        "login": "10/min",
    },
}

# Auditoria basica de autenticacao (RNF). Eventos de login/logout sao
# registrados sem dados sensiveis (nunca a senha).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "atlas": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "atlas_console": {
            "class": "logging.StreamHandler",
            "formatter": "atlas",
        },
    },
    "loggers": {
        "atlas.auth": {
            "handlers": ["atlas_console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ATLAS Vencimentos API",
    "DESCRIPTION": "API para monitoramento de vencimentos de lotes.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
