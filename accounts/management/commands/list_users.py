"""
List all users in the database.
Usage: python manage.py list_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'List all users'

    def handle(self, *args, **options):
        users = User.objects.all()
        
        if not users:
            self.stdout.write(self.style.WARNING('No users found'))
            return
        
        self.stdout.write(f'\nTotal users: {users.count()}\n')
        
        for user in users:
            groups = ', '.join([g.name for g in user.groups.all()])
            self.stdout.write(
                f'  • {user.username:15} | {user.email:30} | '
                f'Groups: {groups or "None":20} | '
                f'Staff: {user.is_staff} | Active: {user.is_active}'
            )
