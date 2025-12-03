"""
Initialize MAST permissions and default groups.
Run this once after initial setup: python manage.py init_permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from accounts.models import MASTPermissions


class Command(BaseCommand):
    help = 'Initialize MAST permissions and default groups'

    def handle(self, *args, **options):
        # Get content type for permissions
        content_type = ContentType.objects.get_for_model(User)
        
        self.stdout.write('Creating MAST permissions...')
        
        # Create all MAST permissions
        permissions = {}
        for codename, name in MASTPermissions.get_all_permissions():
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            permissions[codename] = perm
            if created:
                self.stdout.write(f'  ✓ Created: {codename}')
            else:
                self.stdout.write(f'  - Exists: {codename}')
        
        self.stdout.write('\nCreating default groups...')
        
        # Create default groups with permissions
        groups_config = [
            {
                'name': 'Administrators',
                'permissions': [
                    MASTPermissions.CAN_VIEW,
                    MASTPermissions.CAN_CHANGE_CONFIGURATION,
                    MASTPermissions.CAN_USE_CONTROLS,
                    MASTPermissions.CAN_CHANGE_USERS,
                    MASTPermissions.CAN_OWN_TASKS,
                ]
            },
            {
                'name': 'Operators',
                'permissions': [
                    MASTPermissions.CAN_VIEW,
                    MASTPermissions.CAN_USE_CONTROLS,
                    MASTPermissions.CAN_OWN_TASKS,
                ]
            },
            {
                'name': 'Observers',
                'permissions': [
                    MASTPermissions.CAN_VIEW,
                    MASTPermissions.CAN_OWN_TASKS,
                ]
            },
            {
                'name': 'Viewers',
                'permissions': [
                    MASTPermissions.CAN_VIEW,
                ]
            },
        ]
        
        for group_config in groups_config:
            group, created = Group.objects.get_or_create(name=group_config['name'])
            
            # Clear and set permissions
            group.permissions.clear()
            for perm_code in group_config['permissions']:
                group.permissions.add(permissions[perm_code])
            
            if created:
                self.stdout.write(f'  ✓ Created group: {group_config["name"]}')
            else:
                self.stdout.write(f'  - Updated group: {group_config["name"]}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Initialization complete!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('  1. Create superuser: python manage.py createsuperuser')
        self.stdout.write('  2. Or create user: python manage.py create_user <username>')
