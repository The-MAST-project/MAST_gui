"""
Create a MAST user with groups.
Usage: python manage.py create_user username --email user@example.com --groups "Administrators,Operators"
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Create a MAST user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('--email', type=str, help='Email address')
        parser.add_argument('--first-name', type=str, help='First name')
        parser.add_argument('--groups', type=str, help='Comma-separated group names')
        parser.add_argument('--password', type=str, help='Password (will prompt if not provided)')

    def handle(self, *args, **options):
        username = options['username']
        email = options.get('email', '')
        first_name = options.get('first_name', '')
        password = options.get('password')
        groups_str = options.get('groups', '')
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists')
        
        # Get password if not provided
        if not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            if password != password_confirm:
                raise CommandError('Passwords do not match')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
        )
        
        self.stdout.write(f'✓ Created user: {username}')
        
        # Add to groups
        if groups_str:
            group_names = [g.strip() for g in groups_str.split(',')]
            for group_name in group_names:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    self.stdout.write(f'  ✓ Added to group: {group_name}')
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  ✗ Group not found: {group_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ User {username} created successfully!'))
