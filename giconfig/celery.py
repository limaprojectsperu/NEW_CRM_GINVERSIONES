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
    # Responder automáticamente, si un usuario no respondió 
    'respond-automatically': {
        'task': 'apps.tasks.respond_automatically_task',
        'schedule': 120.0,  # cada 2 minutos
    },
    # Envío de plantillas programadas
    'next-template': {
        'task': 'apps.tasks.send_scheduled_templates_task',
        'schedule': 60.0,  # CADA 1 MINUTO para precisión
    },
}

app.conf.timezone = 'America/Lima'

# CONFIGURACIONES ADICIONALES RECOMENDADAS para mejor rendimiento
app.conf.update(
    # Evitar que las tareas se acumulen si hay retrasos
    worker_prefetch_multiplier=1,
    
    # Configurar límites de tiempo para evitar tareas colgadas
    task_soft_time_limit=300,  # 5 minutos límite suave
    task_time_limit=600,       # 10 minutos límite duro
    
    # Mejorar la precisión del beat scheduler
    beat_max_loop_interval=30,  # Chequear cada 30 segundos máximo
)