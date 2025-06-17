# apps/management/commands/messenger_scheduled_task.py
import requests
from requests.exceptions import RequestException
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import Users, Permissions, Perfiles, PerfilPermissions

class Command(BaseCommand):
    help = 'Limpia tablas e importa datos desde APIs externas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando importación de datos...'))
        
        # Configuración de fuentes
        fuentes = {
            'users': {
                'url': 'https://sistema.grupoimagensac.com.pe/api/usuarios',
                'model': Users,
                'pk': 'co_usuario',
                'wrapper_key': 'data',
            },
            'permissions': {
                'url': 'https://sistema.grupoimagensac.com.pe/api/permisos',
                'model': Permissions,
                'pk': 'id',
                'wrapper_key': 'data',
            },
            'perfiles': {
                'url': 'https://sistema.grupoimagensac.com.pe/api/roles',
                'model': Perfiles,
                'pk': 'co_perfil',
                'wrapper_key': 'data',
            },
            'perfil_permissions': {
                'url': 'https://sistema.grupoimagensac.com.pe/api/roles-permisos',
                'model': PerfilPermissions,
                'pk': 'id',
                'wrapper_key': 'data',
            },
        }

        # Limpiar tablas primero
        self.stdout.write('Eliminando registros existentes...')
        try:
            with transaction.atomic():
                # Orden importante: eliminar dependencias primero
                PerfilPermissions.objects.all().delete()
                Users.objects.all().delete()
                Permissions.objects.all().delete()
                Perfiles.objects.all().delete()
                
            self.stdout.write(self.style.SUCCESS('Registros eliminados correctamente'))
        except Exception as e:
            error_msg = f'Error al eliminar registros: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            print(f"ERROR: {error_msg}")
            return f"Error: {error_msg}"

        # Importar datos
        resumen = {}
        errores_totales = 0

        for nombre, cfg in fuentes.items():
            self.stdout.write(f'Procesando {nombre}...')
            
            try:
                # Realizar petición HTTP
                resp = requests.get(cfg['url'], timeout=30)
                resp.raise_for_status()
                
                # Parsear JSON
                try:
                    payload = resp.json()
                except ValueError as e:
                    error_msg = f"Respuesta no JSON en '{nombre}': {str(e)}"
                    self.stdout.write(self.style.ERROR(error_msg))
                    print(f"ERROR: {error_msg}")
                    errores_totales += 1
                    continue

                # Extraer datos
                datos = payload.get(cfg.get('wrapper_key')) if isinstance(payload, dict) else payload
                
                if not isinstance(datos, list):
                    error_msg = f"Formato inesperado en '{nombre}', se esperaba lista"
                    self.stdout.write(self.style.ERROR(error_msg))
                    print(f"ERROR: {error_msg}")
                    errores_totales += 1
                    continue

                # Procesar cada elemento
                contador = 0
                errores_item = 0
                
                for item in datos:
                    if not isinstance(item, dict):
                        errores_item += 1
                        continue
                        
                    pk_val = item.get(cfg['pk'])
                    if pk_val is None:
                        errores_item += 1
                        continue

                    try:
                        # Upsert con transacción
                        with transaction.atomic():
                            cfg['model'].objects.update_or_create(
                                **{cfg['pk']: pk_val},
                                defaults=item
                            )
                        contador += 1
                    except Exception as e:
                        errores_item += 1
                        error_msg = f"Error procesando item {pk_val} en {nombre}: {str(e)}"
                        self.stdout.write(self.style.WARNING(error_msg))
                        print(f"WARNING: {error_msg}")

                resumen[nombre] = {
                    'procesados': contador,
                    'errores': errores_item,
                    'total_items': len(datos)
                }
                
                success_msg = f'{nombre}: {contador} registros procesados, {errores_item} errores'
                self.stdout.write(self.style.SUCCESS(success_msg))
                print(f"SUCCESS: {success_msg}")

            except RequestException as e:
                error_msg = f"Error al conectar a '{nombre}': {str(e)}"
                self.stdout.write(self.style.ERROR(error_msg))
                print(f"ERROR: {error_msg}")
                resumen[nombre] = {'error': error_msg}
                errores_totales += 1

        # Resumen final
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN DE IMPORTACIÓN ==='))
        print("\n=== RESUMEN DE IMPORTACIÓN ===")
        
        for nombre, info in resumen.items():
            if 'error' in info:
                msg = f'{nombre}: {info["error"]}'
                self.stdout.write(self.style.ERROR(msg))
                print(f"ERROR: {msg}")
            else:
                msg = f'{nombre}: {info["procesados"]}/{info["total_items"]} registros importados'
                self.stdout.write(self.style.SUCCESS(msg))
                print(f"SUCCESS: {msg}")

        if errores_totales > 0:
            final_msg = f'Importación completada con {errores_totales} errores'
            self.stdout.write(self.style.WARNING(final_msg))
            print(f"WARNING: {final_msg}")
            return final_msg
        
        final_msg = 'Importación completada exitosamente'
        self.stdout.write(self.style.SUCCESS(final_msg))
        print(f"SUCCESS: {final_msg}")
        return final_msg