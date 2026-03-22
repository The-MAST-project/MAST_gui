from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_user_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'permissions': [
                ('can_view', 'Can view MAST pages'),
                ('can_change_configuration', 'Can change configuration'),
                ('can_use_controls', 'Can use controls'),
                ('can_manage_users', 'Can manage users'),
                ('can_manage_plans', 'Can manage plans'),
                ('can_submit_plans', 'Can submit observation plans'),
            ]},
        ),
    ]
