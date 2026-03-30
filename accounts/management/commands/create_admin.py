"""
Bootstrap the first MAST admin user.
Creates the user, assigns to Admin group, sets is_staff.
Run after: python manage.py migrate && python manage.py init_mast_groups

Usage:
  python manage.py create_admin --username mast --email admin@example.com
"""
from getpass import getpass

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = 'Bootstrap the first MAST admin user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True)
        parser.add_argument('--email', type=str, default='')
        parser.add_argument('--password', type=str, default=None)

    def handle(self, *args, **options):
        username = options['username']

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists')

        try:
            admin_group = Group.objects.get(name='Admin')
        except Group.DoesNotExist:
            raise CommandError('Admin group not found — run init_mast_groups first')

        password = options['password']
        if not password:
            password = getpass('Password: ')
            if password != getpass('Password (again): '):
                raise CommandError('Passwords do not match')

        user = User.objects.create_user(
            username=username,
            email=options['email'],
            password=password,
            is_active=True,
            is_staff=True,   # required for Django /admin/ access
        )
        user.groups.add(admin_group)  # signal will keep is_staff in sync going forward

        self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created and added to Admin group.'))
