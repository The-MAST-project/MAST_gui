"""
Export active users to a JSON file readable by mast-plan-find.

Usage: python manage.py export_users
Output: /Storage/mast-share/MAST/plans/files/users.json
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from accounts.models import User

USERS_JSON = Path('/Storage/mast-share/MAST/plans/files/users.json')


class Command(BaseCommand):
    help = 'Export active registered users to plans/files/users.json'

    def handle(self, *args, **options):
        USERS_JSON.parent.mkdir(parents=True, exist_ok=True)
        users = [
            {'uuid': str(u.uid), 'display': u.display}
            for u in User.objects.filter(is_active=True).exclude(display='')
        ]
        USERS_JSON.write_text(json.dumps(users, indent=2))
        self.stdout.write(self.style.SUCCESS(
            f'Exported {len(users)} users → {USERS_JSON}'
        ))
