import os

from django.core.management.base import BaseCommand, CommandError

from catalogo.models import Usuario


class Command(BaseCommand):
    help = "Cria o administrador ou atualiza a senha dele a partir das variaveis de ambiente."

    def handle(self, *args, **opcoes):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip().lower()
        senha = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        nome = os.environ.get("DJANGO_SUPERUSER_NOME", "").strip() or "Administrador"
        if not email or not senha:
            self.stdout.write("DJANGO_SUPERUSER_EMAIL ou DJANGO_SUPERUSER_PASSWORD vazio; administrador nao foi alterado.")
            return
        if senha != senha.strip():
            raise CommandError("DJANGO_SUPERUSER_PASSWORD tem espacos no inicio ou no fim.")

        usuario = Usuario.objects.filter(email__iexact=email).first()
        criado = usuario is None
        if criado:
            usuario = Usuario(email=email, nome=nome)
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.is_active = True
        usuario.set_password(senha)
        usuario.save()
        acao = "criado" if criado else "atualizado"
        self.stdout.write(self.style.SUCCESS(f"Administrador {email} {acao}."))