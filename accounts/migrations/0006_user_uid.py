import uuid
from django.db import migrations, models


def populate_uid(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        user.uid = uuid.uuid4()
        user.save(update_fields=['uid'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_add_can_execute_plans'),
    ]

    operations = [
        # 1. Add nullable — SQLite can't assign unique defaults to existing rows in one step
        migrations.AddField(
            model_name='user',
            name='uid',
            field=models.UUIDField(null=True, editable=False),
        ),
        # 2. Populate each existing row with a distinct UUID
        migrations.RunPython(populate_uid, migrations.RunPython.noop),
        # 3. Now safe to enforce unique + non-null
        migrations.AlterField(
            model_name='user',
            name='uid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True),
        ),
    ]
