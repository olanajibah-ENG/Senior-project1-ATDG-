from django.core.management.base import BaseCommand

from core_upm.models.user import Role


class Command(BaseCommand):
    help = "Create default roles (DEVELOPER, ADMIN, REVIEWER) if they do not exist."

    def handle(self, *args, **options):
        role_defs = [
            {
                "role_name": "Developer",
                "role_type": "DEVELOPER",
                "description": "Default role for regular developers.",
            },
            {
                "role_name": "Admin",
                "role_type": "ADMIN",
                "description": "Administrator role with full access.",
            },
            {
                "role_name": "Reviewer",
                "role_type": "REVIEWER",
                "description": "Reviewer role with access to review and comment.",
            },
        ]

        created_types = []
        for rd in role_defs:
            role, created = Role.objects.get_or_create(
                role_type=rd["role_type"],
                defaults={
                    "role_name": rd["role_name"],
                    "description": rd["description"],
                },
            )
            if created:
                created_types.append(rd["role_type"])

        if created_types:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Roles created: {', '.join(created_types)}")
            )
        else:
            self.stdout.write("Roles already exist — skipped.")
