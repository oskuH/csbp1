# Generated by Django 5.0.3 on 2024-10-23 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('abilityhub', '0008_alter_log_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='event_code',
            field=models.CharField(default='required', max_length=50),
            preserve_default=False,
        ),
    ]
