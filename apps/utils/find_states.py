from apps.redes_sociales.models import EstadoLead

def find_state_id(red_social, name):
    lead = EstadoLead.objects.filter(red_social=red_social, Nombre=name).first()
    if lead:
        return lead.IDEL
    return None