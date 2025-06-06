# Generated by Django 5.1.6 on 2025-06-05 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0002_whatsappconfiguracion_openai'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsapp',
            name='openai',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='whatsappmensajes',
            name='origen',
            field=models.IntegerField(blank=True, db_column='origen', default=1, help_text='1: default, 2: openai', null=True),
        ),
    ]
