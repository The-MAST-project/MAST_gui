from django.db import migrations


def rename_permission(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    Permission.objects.filter(
        codename='can_execute_plans',
        content_type__app_label='accounts',
    ).update(name='Can execute plans')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_drop_is_registered'),
    ]

    operations = [
        migrations.RunPython(rename_permission, migrations.RunPython.noop),
    ]
