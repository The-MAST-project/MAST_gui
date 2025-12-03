"""
Management command to sync MongoDB groups/capabilities to Django Groups/Permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from common.config import Config
from common.config.identification import UserCapabilities


class Command(BaseCommand):
    help = 'Sync MongoDB groups and capabilities to Django'

    def handle(self, *args, **options):
        config = Config()
        
        # Get or create content type for custom permissions
        content_type = ContentType.objects.get_for_model(User)
        
        # Create Django permissions from UserCapabilities enum
        capability_map = {}
        for cap in UserCapabilities:
            perm, created = Permission.objects.get_or_create(
                codename=cap.value,
                defaults={
                    'name': f'Can {cap.value}',
                    'content_type': content_type,
                }
            )
            capability_map[cap.value] = perm
            if created:
                self.stdout.write(f'Created permission: {cap.value}')
        
        # Sync groups from MongoDB
        mongo_groups = config.db.get('groups', [])
        for mongo_group in mongo_groups:
            group, created = Group.objects.get_or_create(name=mongo_group['name'])
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions based on capabilities
            for cap in mongo_group.get('capabilities', []):
                if cap in capability_map:
                    group.permissions.add(capability_map[cap])
            
            self.stdout.write(f'Synced group: {mongo_group["name"]}')
        
        # Sync users
        mongo_users = config.get_users()
        for mongo_user in mongo_users:
            user, created = User.objects.get_or_create(
                username=mongo_user.name,
                defaults={
                    'email': mongo_user.email or '',
                    'first_name': mongo_user.full_name or '',
                }
            )
            
            # Clear and set groups
            user.groups.clear()
            for group_name in mongo_user.groups:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    pass
            
            if created:
                self.stdout.write(f'Created user: {mongo_user.name}')
            else:
                self.stdout.write(f'Updated user: {mongo_user.name}')
        
        self.stdout.write(self.style.SUCCESS('Sync completed!'))
