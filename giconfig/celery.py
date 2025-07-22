import os
from celery import Celery
from django.conf import settings

# Configurar la variable de entorno para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giconfig.settings')

app = Celery('giconfig')

# Usar configuración de Django para Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscovery de tareas
app.autodiscover_tasks()

# Configuración del beat scheduler
app.conf.beat_schedule = {
    'respond-automatically': {
        'task': 'apps.tasks.respond_automatically_task',
        'schedule': 120.0,  # cada 2 minutos
    },
}

app.conf.timezone = 'America/Lima'