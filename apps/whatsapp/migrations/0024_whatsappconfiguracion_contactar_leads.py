# Generated by Django 5.1.6 on 2025-07-18 21:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0023_lead_whatsapchatuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappconfiguracion',
            name='contactar_leads',
            field=models.BooleanField(default=False),
        ),
    ]
