"""
Create a registered MAST user and assign groups.

Usage:
  python manage.py create_user alice --email alice@example.com --groups Scientist
  python manage.py create_user bob   --email bob@example.com   --groups Operator,Scientist
"""
from getpass import getpass

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = 'Create a registered MAST user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)
        parser.add_argument('--email', type=str, default='')
        parser.add_argument('--first-name', type=str, default='')
        parser.add_argument('--last-name', type=str, default='')
        parser.add_argument('--groups', type=str, default='', help='Comma-separated group names')
        parser.add_argument('--password', type=str, default=None)

    def handle(self, *args, **options):
        username = options['username']

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists')

        password = options['password']
        if not password:
            password = getpass('Password: ')
            if password != getpass('Password (again): '):
                raise CommandError('Passwords do not match')

        user = User.objects.create_user(
            username=username,
            email=options['email'],
            password=password,
            first_name=options['first_name'],
            last_name=options['last_name'],
            is_registered=True,
            is_active=True,
        )
        self.stdout.write(f'Created user: {username}')

        for name in [g.strip() for g in options['groups'].split(',') if g.strip()]:
            try:
                user.groups.add(Group.objects.get(name=name))
                self.stdout.write(f'  Added to group: {name}')
            except Group.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Group not found: {name}'))

        self.stdout.write(self.style.SUCCESS('Done.'))
