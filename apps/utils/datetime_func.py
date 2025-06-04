from django.utils import timezone
from datetime import timedelta
import pytz

MESES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def get_naive_peru_time():
    """
    Retorna la hora actual de Perú como datetime naive (sin zona horaria).
    Útil para guardar en campos DateTimeField sin info TZ.
    """
    peru_tz = pytz.timezone('America/Lima')
    utc_now = timezone.now()
    peru_time = utc_now.astimezone(peru_tz)
    # Remover timezone info para el update
    return peru_time.replace(tzinfo=None)

def get_date_time():
    """
    Retorna 09 de mayo de 2025, 14:30
    """
    now = get_naive_peru_time()
    fecha = f"{now.day} de {MESES[now.month]} de {now.year}"
    hora = now.strftime('%H:%M')
    return fecha, hora

def get_naive_peru_time_delta(days=0, hours=0, minutes=0, seconds=0):
    """
    Retorna la hora de Perú con un delta aplicado como datetime naive.
    
    Args:
        days (int): Días a sumar/restar (puede ser negativo)
        hours (int): Horas a sumar/restar
        minutes (int): Minutos a sumar/restar
        seconds (int): Segundos a sumar/restar
    
    Ejemplos:
        get_naive_peru_time_delta(days=-1)  # Ayer
        get_naive_peru_time_delta(days=1)   # Mañana  
        get_naive_peru_time_delta(hours=-2) # Hace 2 horas
    """
    peru_tz = pytz.timezone('America/Lima')
    utc_now = timezone.now()
    peru_time = utc_now.astimezone(peru_tz)
    
    # Aplicar el delta
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    peru_time_with_delta = peru_time + delta
    
    # Remover timezone info
    return peru_time_with_delta.replace(tzinfo=None)
