# Generated by Django 5.1.6 on 2025-07-15 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0013_alter_whatsappconfiguracion_url_graph_v'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappplantillaresumen',
            name='origen_datos',
            field=models.CharField(blank=True, db_column='origen_datos', max_length=50, null=True),
        ),
    ]
