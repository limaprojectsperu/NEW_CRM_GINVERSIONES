from celery import shared_task
from django.core.management import call_command
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def respond_automatically_task(self):
    """Ejecuta el comando cada 2 minutos"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Iniciando tarea de respuesta automática...")
        
        # Ejecutar el comando Django
        call_command('respond_automatically')

        success_msg = f"[{timestamp}] Tarea de respuesta automática ejecutada correctamente"
        logger.info(success_msg)

        # Ejecutar el analisis del historial del chat
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Iniciando tarea de analisis del historial del chat...")

        # Ejecutar el comando Django
        call_command('analyze_chat_new_lead')

        success_msg = f"[{timestamp}] Tarea de analisis del historial del chat ejecutada correctamente"
        logger.info(success_msg)
        
        return success_msg
    except Exception as e:
        error_msg = f"Error ejecutando tarea de respuesta automática: {str(e)}"
        logger.error(error_msg)
        # Re-lanzar la excepción para que Celery la registre como fallo
        raise self.retry(exc=e, countdown=60, max_retries=3)

@shared_task(bind=True)
def send_scheduled_templates_task(self):
    """Envía plantillas programadas cada minuto con ventana de tolerancia"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Iniciando tarea de envío de plantillas programadas...")
        
        # Ejecutar el comando Django existente
        call_command('next_template')
        
        success_msg = f"[{timestamp}] Tarea de envío de plantillas completada"
        logger.info(success_msg)
        
        return success_msg
        
    except Exception as e:
        error_msg = f"Error ejecutando tarea de envío de plantillas: {str(e)}"
        logger.error(error_msg)
        # Reintentar cada 30 segundos, máximo 2 intentos para no saturar
        raise self.retry(exc=e, countdown=30, max_retries=2)

@shared_task
def test_celery_task():
    """Tarea de prueba para verificar que Celery funciona"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] Celery está funcionando correctamente!"
    print(message)
    logger.info(message)
    return message