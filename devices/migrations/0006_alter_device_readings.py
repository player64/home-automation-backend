# Generated by Django 3.2.6 on 2021-08-11 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0005_alter_device_updated_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='readings',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
