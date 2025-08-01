from apps.redes_sociales.models import EstadoLead

def find_state_id(red_social, IDRedSocial, name):
    lead = EstadoLead.objects.filter(red_social=red_social, Nombre=name)
    
    if IDRedSocial > 0:
        lead = lead.filter(IDRedSocial=IDRedSocial)
    
    lead = lead.first() 
    
    if lead:
        return lead.IDEL
    
    return None