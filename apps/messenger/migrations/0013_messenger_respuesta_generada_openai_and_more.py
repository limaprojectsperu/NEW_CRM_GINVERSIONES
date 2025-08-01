# Generated by Django 5.1.6 on 2025-07-21 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0012_messengermensaje_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='messenger',
            name='respuesta_generada_openai',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='messengermensaje',
            name='origen',
            field=models.IntegerField(blank=True, db_column='origen', default=1, help_text='1:enviados, 2: recibidos, 3: openai', null=True),
        ),
    ]
