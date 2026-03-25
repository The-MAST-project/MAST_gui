"""
Create/update MAST groups with their canonical permission sets.
Safe to run multiple times — idempotent.

Usage: python manage.py init_mast_groups
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

from accounts.models import MASTPermissions

GROUPS = {
    'Everybody': [
        MASTPermissions.CAN_VIEW,
    ],
    'Scientist': [
        MASTPermissions.CAN_VIEW,
        MASTPermissions.CAN_SUBMIT_PLANS,
    ],
    'Operator': [
        MASTPermissions.CAN_VIEW,
        MASTPermissions.CAN_SUBMIT_PLANS,
        MASTPermissions.CAN_MANAGE_PLANS,
        MASTPermissions.CAN_EXECUTE_PLANS,
        MASTPermissions.CAN_USE_CONTROLS,
    ],
    'Admin': [
        MASTPermissions.CAN_VIEW,
        MASTPermissions.CAN_SUBMIT_PLANS,
        MASTPermissions.CAN_MANAGE_PLANS,
        MASTPermissions.CAN_EXECUTE_PLANS,
        MASTPermissions.CAN_USE_CONTROLS,
        MASTPermissions.CAN_CHANGE_CONFIGURATION,
        MASTPermissions.CAN_MANAGE_USERS,
    ],
}


class Command(BaseCommand):
    help = 'Create/update MAST groups with their canonical permission sets'

    def handle(self, *args, **options):
        for group_name, codenames in GROUPS.items():
            perms = Permission.objects.filter(codename__in=codenames, content_type__app_label='accounts')
            found = set(perms.values_list('codename', flat=True))
            missing = set(codenames) - found
            if missing:
                self.stdout.write(self.style.WARNING(
                    f'  Warning: permissions not found (run migrate first?): {missing}'
                ))

            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.set(perms)

            verb = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'  {verb} group "{group_name}" → {sorted(found)}'))

        self.stdout.write(self.style.SUCCESS('\nDone. Run create_admin to bootstrap the first admin user.'))
