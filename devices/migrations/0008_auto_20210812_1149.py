# Generated by Django 3.2.6 on 2021-08-12 10:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0007_alter_device_gpio'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workspace',
            name='devices',
        ),
        migrations.AddField(
            model_name='device',
            name='workspace',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='devices.workspace'),
        ),
    ]
