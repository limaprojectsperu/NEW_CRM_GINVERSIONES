# views.py
import requests
from requests.exceptions import RequestException
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Users, UserTokens, Permissions, Perfiles, PerfilPermissions

class ImportData(APIView):
    """
    GET /api/import-data/
    Consume varias APIs externas y dispara un upsert en cada tabla.
    """
    def get(self, request):
        fuentes = {
            'users': {
                'url':   'https://sistema.grupoimagensac.com.pe/api/usuarios',
                'model': Users,
                'pk':    'co_usuario',
                'wrapper_key': 'data',
            },
            'tokens': {
                'url':   'https://sistema.grupoimagensac.com.pe/api/token-usuarios',
                'model': UserTokens,
                'pk':    'id',
                'wrapper_key': 'data',
            },
            'permissions': {
                'url':   'https://sistema.grupoimagensac.com.pe/api/permisos',
                'model': Permissions,
                'pk':    'id',
                'wrapper_key': 'data',
            },
            'perfiles': {
                'url':   'https://sistema.grupoimagensac.com.pe/api/roles',
                'model': Perfiles,
                'pk':    'co_perfil',
                'wrapper_key': 'data',
            },
            'perfil_permissions': {
                'url':   'https://sistema.grupoimagensac.com.pe/api/roles-permisos',
                'model': PerfilPermissions,
                'pk':    'id',
                'wrapper_key': 'data',
            },
        }

        resumen = {}

        for nombre, cfg in fuentes.items():
            try:
                resp = requests.get(cfg['url'], timeout=10)
                resp.raise_for_status()
            except RequestException as e:
                return Response(
                    {'error': f"Error al conectar a '{nombre}': {str(e)}"},
                    status=status.HTTP_502_BAD_GATEWAY
                )

            try:
                payload = resp.json()
            except ValueError:
                return Response(
                    {'error': f"Respuesta no JSON en '{nombre}'"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Extrae la lista real
            datos = payload.get(cfg.get('wrapper_key')) if isinstance(payload, dict) else payload
            if not isinstance(datos, list):
                return Response(
                    {'error': f"Formato inesperado en '{nombre}', se esperaba lista"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            contador = 0
            for item in datos:
                if not isinstance(item, dict):
                    # ignoramos entradas que no sean dict
                    continue

                pk_val = item.get(cfg['pk'])
                if pk_val is None:
                    continue

                # upsert
                cfg['model'].objects.update_or_create(
                    **{ cfg['pk']: pk_val },
                    defaults=item
                )
                contador += 1

            resumen[nombre] = contador

        return Response(
            {'message': 'Importación completada', 'detalles': resumen},
            status=status.HTTP_200_OK
        )
