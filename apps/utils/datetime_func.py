from django.utils import timezone
from datetime import timedelta

MESES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def get_naive_peru_time():
    """
    Retorna la hora actual del sistema
    """
    now = timezone.now()
    return now.replace(tzinfo=None)

def get_date_time():
    """
    Retorna la fecha y hora actual en el formato "DD de MES de AAAA, HH:MM".
    Asume que la hora del sistema ya está configurada correctamente.
    """
    now = get_naive_peru_time()
    
    fecha = f"{now.day} de {MESES[now.month]} de {now.year}"
    hora = now.strftime('%H:%M')
    return fecha, hora

def get_naive_peru_time_delta(days=0, hours=0, minutes=0, seconds=0):
    """
    Retorna la hora actual con un delta aplicado como datetime naive.
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
    current_time = timezone.now()
    
    # Aplicar el delta
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    time_with_delta = current_time + delta
    
    # Remover timezone info para obtener un datetime naive
    return time_with_delta.replace(tzinfo=None)