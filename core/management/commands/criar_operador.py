from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Cria um usuario operador para a SPA (autenticacao por JWT). "
        "Usa OPERADOR_USERNAME, OPERADOR_PASSWORD e OPERADOR_EMAIL do ambiente "
        "quando os argumentos nao forem informados."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--username", help="Nome de usuario (default: env OPERADOR_USERNAME)")
        parser.add_argument("--password", help="Senha (default: env OPERADOR_PASSWORD)")
        parser.add_argument("--email", help="E-mail (default: env OPERADOR_EMAIL)")
        parser.add_argument(
            "--staff",
            action="store_true",
            help="Cria usuario com acesso ao admin (superuser).",
        )

    def handle(self, *args, **options) -> None:
        import os

        username = options["username"] or os.getenv("OPERADOR_USERNAME")
        password = options["password"] or os.getenv("OPERADOR_PASSWORD")
        email = options["email"] or os.getenv("OPERADOR_EMAIL") or ""

        if not username or not password:
            raise CommandError(
                "Informe --username e --password (ou as envs OPERADOR_USERNAME/"
                "OPERADOR_PASSWORD)."
            )

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Usuario '{username}' ja existe."))
            return

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=options["staff"],
            is_superuser=options["staff"],
        )
        self.stdout.write(self.style.SUCCESS(f"Usuario operador '{username}' criado."))
