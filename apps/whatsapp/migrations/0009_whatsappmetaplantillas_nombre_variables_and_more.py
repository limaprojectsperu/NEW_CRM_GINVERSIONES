# Generated by Django 5.1.6 on 2025-07-14 21:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0008_whatsappmetaplantillas_mensaje'),
    ]

    operations = [
        migrations.AddField(
            model_name='whatsappmetaplantillas',
            name='nombre_variables',
            field=models.CharField(blank=True, db_column='nombre_variables', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='whatsappmetaplantillas',
            name='variables',
            field=models.IntegerField(blank=True, db_column='variables', null=True),
        ),
        migrations.CreateModel(
            name='WhatsappPlantillaResumen',
            fields=[
                ('id', models.AutoField(db_column='id', primary_key=True, serialize=False)),
                ('enviados', models.CharField(blank=True, db_column='enviados', max_length=100, null=True)),
                ('exitosos', models.CharField(blank=True, db_column='exitosos', max_length=255, null=True)),
                ('fallidos', models.CharField(blank=True, db_column='fallidos', max_length=40, null=True)),
                ('estado', models.IntegerField(db_column='estado', default=1)),
                ('whatsapp_meta_plantillas_id', models.ForeignKey(db_column='whatsapp_meta_plantillas_id', on_delete=django.db.models.deletion.PROTECT, related_name='plantillas', to='whatsapp.whatsappmetaplantillas')),
            ],
            options={
                'verbose_name_plural': 'WhatsApp Plantillas Resumen',
                'db_table': 'whatsapp_plantilla_resumen',
            },
        ),
    ]
