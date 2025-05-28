from django.utils import timezone
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

def get_date_tiem():
    """
    Retorna 09 de mayo de 2025, 14:30
    """
    now = get_naive_peru_time()
    fecha = f"{now.day} de {MESES[now.month]} de {now.year}"
    hora = now.strftime('%H:%M')
    return fecha, hora