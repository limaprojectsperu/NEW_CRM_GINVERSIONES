from django.db import connection
from apps.users.models import UserTokens
from apps.whatsapp.models import WhatsappConfiguracionUser, WhatsapChatUser

# Método alternativo usando SQL raw (más eficiente para consultas complejas)
def get_user_tokens_by_permissions(permission):

    try:
        query = """
        SELECT ut.token
        FROM user_tokens ut
        INNER JOIN users u ON ut.user_id = u.co_usuario
        INNER JOIN perfil_permissions pp ON u.co_perfil = pp.perfil_id
        INNER JOIN permissions p ON pp.permission_id = p.id
        WHERE p.name = %s 
        AND p.state = 1 
        AND ut.state = 1
        AND u.in_estado = 1
        AND ut.token IS NOT NULL
        AND ut.token != ''
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [permission])
            results = cursor.fetchall()
        
        # Extraer solo los tokens del resultado
        tokens = [row[0] for row in results if row[0]]
        
        return tokens
        
    except Exception as e:
        return []
    
def get_user_tokens_by_whatsapp(IDRedSocial, IDChat):
    # 1. Encontrar los IDs de usuarios que pertenecen al CHAT específico.
    users_in_chat = WhatsapChatUser.objects.filter(
        IDChat=IDChat
    ).values('user_id')

    # 2. Encontrar los IDs de usuarios que pertenecen a la CONFIGURACIÓN de la red social
    users_in_config = WhatsappConfiguracionUser.objects.filter(
        IDRedSocial=IDRedSocial,
        user_id__in=users_in_chat  # ¡La clave está aquí! Filtramos por el subquery.
    ).values_list('user_id', flat=True)
    
    # 3. Finalmente, obtenemos los tokens de esos usuarios.
    tokens = UserTokens.objects.filter(
        user_id__in=users_in_config
    ).values_list('token', flat=True)

    return list(tokens)

def get_users_tokens(miembros):

    user_ids = [miembro.user_id for miembro in miembros]
    # Filtrar los UserTokens usando esos user_ids
    user_tokens = UserTokens.objects.filter(user_id__in=user_ids)
    # Extraer solo los tokens del resultado
    tokens = [tokens.token for tokens in user_tokens]
        
    return tokens

def delete_token(token):
    
    UserTokens.objects.filter(token=token).delete()

