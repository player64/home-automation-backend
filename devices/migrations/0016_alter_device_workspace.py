# Generated by Django 3.2.6 on 2021-08-20 13:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0015_alter_device_workspace'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='workspace',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='devices.workspace'),
        ),
    ]
