import getpass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core_upm.models.user import Role


class Command(BaseCommand):
    help = "Create an administrator user account."

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, help="Username for the admin account")
        parser.add_argument("--email", type=str, help="Email for the admin account")
        parser.add_argument("--password", type=str, help="Password for the admin account")
        parser.add_argument(
            "--fullname",
            type=str,
            default="System Admin",
            help="Full name for the admin account",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        email = options.get("email")
        password = options.get("password")
        full_name = options.get("fullname")

        if not username:
            username = input("Admin username: ").strip()

        if not email:
            email = input("Admin email: ").strip()

        if not password:
            password = getpass.getpass("Admin password: ")

        try:
            admin_role = Role.objects.get(role_type="ADMIN")
        except Role.DoesNotExist:
            raise CommandError("ADMIN role does not exist. Run `setup_roles` first.")

        if User.objects.filter(username=username).exists():
            raise CommandError(f"Username '{username}' already exists.")

        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = getattr(user, "profile", None)
            if profile is None:
                # If signals didn't run / profile not created, create one
                from core_upm.models.user import UserProfile

                profile = UserProfile.objects.create(user=user, full_name=username)

            profile.role = admin_role
            profile.full_name = full_name
            profile.save()

        self.stdout.write(self.style.SUCCESS(f"✓ Admin created: {username} | role: ADMIN"))
