# Generated by Django 5.1.6 on 2025-07-21 16:58

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0011_messengerconfiguracion_responder_automaticamente_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='messengermensaje',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
