from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User

class Command(BaseCommand):
    help = "Create default MAST groups and assign permissions"

    GROUPS = [
        # (group_name, [permission_codenames])
        ("Viewers", ["can_view"]),
        ("Configurators", ["can_change_configuration"]),
        ("Controllers", ["can_use_controls"]),
        ("Scientists", ["can_make_plans"]),
        ("Staff", ["can_manage_plans"]),
        # Administrators and Developers handled via is_superuser
    ]

    def handle(self, *args, **options):
        # Get content type for custom User model
        ct = ContentType.objects.get_for_model(User)
        # Ensure all custom permissions exist
        perms = {
            "can_view": Permission.objects.get_or_create(
                codename="can_view",
                name="Can view MAST pages",
                content_type=ct
            )[0],
            "can_change_configuration": Permission.objects.get_or_create(
                codename="can_change_configuration",
                name="Can change configuration",
                content_type=ct
            )[0],
            "can_use_controls": Permission.objects.get_or_create(
                codename="can_use_controls",
                name="Can use controls",
                content_type=ct
            )[0],
            "can_manage_users": Permission.objects.get_or_create(
                codename="can_manage_users",
                name="Can manage users",
                content_type=ct
            )[0],
            "can_manage_plans": Permission.objects.get_or_create(
                codename="can_manage_plans",
                name="Can manage plans",
                content_type=ct
            )[0],
            "can_make_plans": Permission.objects.get_or_create(
                codename="can_make_plans",
                name="Can make plans",
                content_type=ct
            )[0],
        }

        for group_name, perm_codes in self.GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()
            for code in perm_codes:
                group.permissions.add(perms[code])
            group.save()
            self.stdout.write(self.style.SUCCESS(
                f"Group '{group_name}' created/updated with permissions: {perm_codes}"
            ))

        self.stdout.write(self.style.SUCCESS("MAST groups and permissions initialized."))

        # Info for admins/developers
        self.stdout.write(self.style.WARNING(
            "Administrators and Developers should be assigned is_superuser=True (all permissions)."
        ))
