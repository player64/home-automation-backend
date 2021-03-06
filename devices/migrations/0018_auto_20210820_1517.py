# Generated by Django 3.2.6 on 2021-08-20 14:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0017_devicelog'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='devicelog',
            options={'ordering': ['-time']},
        ),
        migrations.AlterField(
            model_name='devicelog',
            name='time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.CreateModel(
            name='DeviceEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('type', models.CharField(choices=[('time', 'Time'), ('sensor', 'Sensor')], default='time', max_length=20)),
                ('action', models.CharField(choices=[('ON', 'ON'), ('OFF', 'OFF')], default='OFF', max_length=10)),
                ('time', models.TimeField(blank=True, null=True)),
                ('reading_type', models.CharField(blank=True, choices=[('=', '='), ('>', '>'), ('>=', '>='), ('<=', '<='), ('<', '<')], max_length=40, null=True)),
                ('rule', models.CharField(blank=True, max_length=3, null=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='devices.device')),
                ('sensor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sensor', to='devices.device')),
            ],
        ),
    ]
