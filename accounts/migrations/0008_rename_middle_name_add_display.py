from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_add_middle_name_remove_full_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='middle_name',
            new_name='middle',
        ),
        migrations.AddField(
            model_name='user',
            name='display',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
