# Generated by Django 5.1.6 on 2025-06-05 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0003_messenger_openai_messengermensaje_origen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messenger',
            name='openai',
            field=models.BooleanField(default=True),
        ),
    ]
