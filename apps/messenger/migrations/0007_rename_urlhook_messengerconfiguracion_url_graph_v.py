# Generated by Django 5.1.6 on 2025-07-15 17:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0006_messengerconfiguracion_openai_analizador'),
    ]

    operations = [
        migrations.RenameField(
            model_name='messengerconfiguracion',
            old_name='urlHook',
            new_name='url_graph_v',
        ),
    ]
