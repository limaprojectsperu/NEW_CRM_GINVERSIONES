# Generated by Django 5.1.6 on 2025-07-15 22:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whatsapp', '0015_alter_whatsappplantillaresumen_enviados_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsappConfiguracionUser',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('IDRedSocial', models.IntegerField()),
                ('user_id', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'WhatsApp Configuracion Usuario',
                'db_table': 'whatsapp_configuracion_user',
            },
        ),
    ]
