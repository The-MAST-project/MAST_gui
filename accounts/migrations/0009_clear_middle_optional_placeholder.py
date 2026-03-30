from django.db import migrations


def clear_optional_placeholder(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(middle='Optional').update(middle='')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_rename_middle_name_add_display'),
    ]

    operations = [
        migrations.RunPython(clear_optional_placeholder, migrations.RunPython.noop),
    ]
