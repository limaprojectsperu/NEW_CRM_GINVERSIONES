from django.db import migrations, models

def remove_unique_together(apps, schema_editor):
    # No necesitas hacer nada aquí, solo quieres que Django omita la operación
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('chat_interno', '0003_remove_chatinternomiembro_nombre'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChatInternoConfiguracion',
        ),
        migrations.RunPython(
            remove_unique_together,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='chatinterno',
            name='IDEL',
        ),
        migrations.RemoveField(
            model_name='chatinterno',
            name='IDRedSocial',
        ),
        migrations.RemoveField(
            model_name='chatinterno',
            name='IDSubEstadoLead',
        ),
        migrations.AddField(
            model_name='chatinternomiembro',
            name='IDEL',
            field=models.IntegerField(blank=True, db_column='IDEL', help_text='ID estado', null=True),
        ),
    ]