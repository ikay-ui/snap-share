# Generated by Django 4.2.17 on 2025-01-08 14:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('folders', '0013_alter_folder_expires_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='folder',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 1, 10, 14, 26, 27, 449948, tzinfo=datetime.timezone.utc)),
        ),
    ]