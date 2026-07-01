"""Ponto WSGI compativel para servidores que procuram o modulo app."""

from config.wsgi import application

__all__ = ["application"]
