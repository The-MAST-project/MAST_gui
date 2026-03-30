"""
Create mockup Django users for testing the plans workflow.
Safe to run multiple times — idempotent.

Usage: python manage.py create_mockup_users
"""
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.models import User, unique_display

MOCKUP_USERS = [
    {
        'username':   'mockup.scientist',
        'first_name': 'Mockup',
        'last_name':  'Scientist',
        'email':      'mockup.scientist@mast.local',
        'groups':     ['Everybody', 'Scientist'],
    },
    {
        'username':   'mockup.operator',
        'first_name': 'Mockup',
        'last_name':  'Operator',
        'email':      'mockup.operator@mast.local',
        'groups':     ['Everybody', 'Operator'],
    },
]


class Command(BaseCommand):
    help = 'Create mockup users for plans workflow testing'

    def handle(self, *args, **options):
        for spec in MOCKUP_USERS:
            user, created = User.objects.get_or_create(
                username=spec['username'],
                defaults=dict(
                    first_name=spec['first_name'],
                    last_name=spec['last_name'],
                    email=spec['email'],
                    is_active=True,
                    display=unique_display(spec['first_name'], spec['last_name']),
                ),
            )
            if created:
                user.set_unusable_password()
                user.save()
                verb = 'Created'
            else:
                verb = 'Already exists'

            for group_name in spec['groups']:
                try:
                    user.groups.add(Group.objects.get(name=group_name))
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  Group not found: {group_name} (run init_mast_groups first)'
                    ))

            self.stdout.write(self.style.SUCCESS(
                f'  {verb}: {user.username}  display={user.display}  uid={user.uid}'
            ))

        self.stdout.write(self.style.SUCCESS('\nDone.'))
