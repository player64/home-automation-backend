# Generated by Django 3.2.6 on 2021-08-10 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='device',
            options={'ordering': ['type']},
        ),
        migrations.AddField(
            model_name='device',
            name='readings',
            field=models.JSONField(blank=True, default=None),
        ),
    ]
