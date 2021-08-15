# Generated by Django 3.2.6 on 2021-08-15 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0009_alter_device_workspace'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventHubMsg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]