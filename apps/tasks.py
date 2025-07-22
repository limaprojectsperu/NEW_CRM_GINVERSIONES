from celery import shared_task
from django.core.management import call_command
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def respond_automatically_task(self):
    """Ejecuta el comando de respuesta automática cada 2 minutos"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Iniciando tarea de respuesta automática...")
        
        # Ejecutar el comando Django
        call_command('respond_automatically')
        
        success_msg = f"[{timestamp}] Tarea de respuesta automática ejecutada correctamente"
        logger.info(success_msg)
        print(success_msg)  # También imprimir en consola
        
        return success_msg
    except Exception as e:
        error_msg = f"Error ejecutando tarea de respuesta automática: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        # Re-lanzar la excepción para que Celery la registre como fallo
        raise self.retry(exc=e, countdown=60, max_retries=3)

@shared_task(bind=True)
def import_data_task(self):
    """Ejecuta el comando de importación de datos"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"[{timestamp}] Iniciando tarea de importación de datos...")
        
        # Ejecutar el comando Django
        result = call_command('import_data_task')
        
        success_msg = f"[{timestamp}] Tarea de importación completada: {result}"
        logger.info(success_msg)
        print(success_msg)
        
        return success_msg
    except Exception as e:
        error_msg = f"Error ejecutando tarea de importación: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        raise self.retry(exc=e, countdown=300, max_retries=2)  # Reintentar en 5 minutos

@shared_task
def test_celery_task():
    """Tarea de prueba para verificar que Celery funciona"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] Celery está funcionando correctamente!"
    print(message)
    logger.info(message)
    return message