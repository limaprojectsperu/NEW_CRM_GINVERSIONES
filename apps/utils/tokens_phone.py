from django.db import connection

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

