from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_rename_can_execute_plans'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar_url',
            field=models.URLField(blank=True, default=''),
        ),
    ]
