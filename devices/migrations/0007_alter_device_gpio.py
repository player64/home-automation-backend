# Generated by Django 3.2.6 on 2021-08-11 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0006_alter_device_readings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='gpio',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
