import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.utils.datetime_func import get_date_time
from django.test import RequestFactory
from rest_framework.parsers import JSONParser
from rest_framework.request import Request

from apps.whatsapp.views.whatsapp_app import WhatsappSendAPIView
from apps.whatsapp.models import WhatsappConfiguracion, Whatsapp
from apps.users.models import Users

class Command(BaseCommand):
    help = 'Envía plantillas automáticamente según la fecha programada'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando proceso de envío automático de plantillas...'))
        
        # Obtener la fecha y hora actual en timezone de Perú
        now = timezone.now()
        
        # Ventana de tiempo de 1 minuto hacia atrás
        time_window_start = now - timedelta(minutes=1)
        
        # Buscar chats que tienen fecha_proxima_plantilla en la ventana de tiempo
        chats_to_send = Whatsapp.objects.filter(
            # Plantillas que deberían enviarse ahora o en el último minuto
            fecha_proxima_plantilla__lte=now,
            fecha_proxima_plantilla__gte=time_window_start,
            fecha_proxima_plantilla__isnull=False,
            Estado=1  # Solo chats activos
        ).select_related().order_by('fecha_proxima_plantilla')  # Ordenar por fecha
        
        total_found = chats_to_send.count()
        total_sent = 0
        total_errors = 0
        
        self.stdout.write(f'Se encontraron {total_found} plantillas programadas para enviar')
        
        for chat in chats_to_send:
            try:
                # Obtener la configuración de WhatsApp para este chat
                setting = WhatsappConfiguracion.objects.get(
                    IDRedSocial=chat.IDRedSocial,
                    Estado=1
                )
                
                # Enviar la plantilla
                response = self.send_message_whatsapp(setting, chat, 'plantilla', origen=1)
                
                if response and response.status_code == 200:
                    total_sent += 1
                    
                    # IMPORTANTE: Limpiar la fecha programada después del envío exitoso
                    chat.fecha_proxima_plantilla = None
                    chat.user_id_proxima_plantilla = None
                    chat.template_name = None
                    chat.template_params = None
                    chat.save(update_fields=[
                        'fecha_proxima_plantilla', 
                        'user_id_proxima_plantilla',
                        'template_name',
                        'template_params'
                    ])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Plantilla enviada a {chat.Nombre} ({chat.Telefono}) - '
                            f'Programada: {chat.fecha_proxima_plantilla}'
                        )
                    )
                else:
                    total_errors += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Error en respuesta del API para {chat.Nombre} ({chat.Telefono})'
                        )
                    )
                    
            except WhatsappConfiguracion.DoesNotExist:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ No se encontró configuración para IDRedSocial: {chat.IDRedSocial}'
                    )
                )
                continue
                
            except Exception as e:
                total_errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error procesando chat {chat.IDChat} ({chat.Nombre}): {str(e)}'
                    )
                )
                continue
        
        # Resultado final
        result_msg = f"Completado - {total_sent} plantillas enviadas, {total_errors} errores de {total_found} encontradas"
        
        self.stdout.write(
            self.style.SUCCESS(result_msg)
        )
        
        return result_msg

    def send_message_whatsapp(self, setting, chat, mensaje, origen=1):
        """Envía mensaje usando WhatsappSendAPIView"""
        try:
            user = Users.objects.filter(co_usuario=chat.user_id_proxima_plantilla).first()
            Fecha, Hora = get_date_time()

            message_data = {
                "IDRedSocial": setting.IDRedSocial,
                "tokenHook": setting.TokenHook,  
                "phone": chat.Telefono,
                "IDChat": chat.IDChat,
                "Telefono": setting.Telefono,
                "Mensaje": mensaje,
                "Fecha": Fecha,
                "Hora": Hora,
                "origen": origen,
                "message_24_hours": True,
                "template_params": chat.template_params.split('*'),
                "template_name": chat.template_name,
            }
            
            factory = RequestFactory()
            django_request = factory.post(
                '/api/whatsapp-app/send-message/',
                data=json.dumps(message_data),
                content_type='application/json'
            )
            
            drf_request = Request(django_request, parsers=[JSONParser()])
            view = WhatsappSendAPIView()
            response = view.post(drf_request)
            return response
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error enviando mensaje WhatsApp: {str(e)}')
            )
            return None