import requests
import json
import os
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.whatsapp.models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes, WhatsapChatUser, WhatsapChatUserHistorial, Lead
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.openai.analyze_chat_funct import analyze_chat_improved
from apps.redes_sociales.models import Marca
from apps.whatsapp.serializers import LeadSerializer
from django.shortcuts import get_object_or_404
from apps.users.models import Users
from apps.utils.tokens_phone import get_tokens_by_user

class Command(BaseCommand):
    help = 'Analiza el chat de un nuevo lead y envía los datos extraídos a la API externa'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando proceso de analisis de procesos...'))

        try:
            # 1. Primero buscar usuarios con respuesta automática habilitada
            usuarios_auto_respuesta = Users.objects.filter(
                co_perfil=38,
                in_estado=1  # Solo usuarios activos
            )

            if not usuarios_auto_respuesta.exists():
                self.stdout.write('No hay usuarios con perfil 38')
                return

            for usuario in usuarios_auto_respuesta:
                self.stdout.write(f'Procesando usuario: {usuario.name} (ID: {usuario.co_usuario})')
                
                # 2. Obtener los chats asignados a este usuario específico
                chats_usuario = WhatsapChatUser.objects.filter(
                    user_id=usuario.co_usuario
                ).values_list('IDChat', flat=True)

                if not chats_usuario:
                    self.stdout.write(f'Usuario {usuario.name} no tiene chats asignados')
                    continue
                
                # 3. Calcular tiempos para respuesta automática
                tiempo_ahora = timezone.now()
                minutos_respuesta = 8
                tiempo_minimo_antiguedad = tiempo_ahora - timedelta(minutes=minutos_respuesta)
                tiempo_maximo_antiguedad = tiempo_ahora - timedelta(minutes=660)

                # 4. Buscar mensajes candidatos de los chats asignados al usuario
                mensajes_candidatos = WhatsappMensajes.objects.filter(
                    IDChat__in=Whatsapp.objects.filter(
                        IDChat__in=chats_usuario,
                        lead_reasignado=False,
                        Estado=1  # Solo chats activos
                    ).values_list('IDChat', flat=True),
                    origen=3,  # Mensaje de IA
                    created_at__lte=tiempo_minimo_antiguedad,
                    created_at__gt=tiempo_maximo_antiguedad
                ).order_by('IDChat', '-created_at')

                if not mensajes_candidatos.exists():
                    self.stdout.write(f'No hay mensajes candidatos para el usuario {usuario.name}')
                    continue

                # 5. Agrupar por chat para verificar si es el último mensaje
                chats_procesados = set()

                for mensaje in mensajes_candidatos:
                    if mensaje.IDChat in chats_procesados:
                        continue

                    # 6. Verificar si es el último mensaje del chat
                    ultimo_mensaje = WhatsappMensajes.objects.filter(
                        IDChat=mensaje.IDChat
                    ).order_by('-created_at').first()

                    if ultimo_mensaje and ultimo_mensaje.IDChatMensaje == mensaje.IDChatMensaje:
                        # Es el último mensaje y es de la IA, generar respuesta
                        try:
                            chat = Whatsapp.objects.get(IDChat=mensaje.IDChat)
                            
                            # Obtener la configuración de WhatsApp asociada al chat
                            config = WhatsappConfiguracion.objects.get(
                                IDRedSocial=chat.IDRedSocial,
                                Estado=1
                            )

                            self.stdout.write(
                                f'Analizando Chat por usuario {usuario.name} '
                                f'a WhatsApp chat {chat.IDChat} - {chat.Nombre}'
                            )

                            # CORRECCIÓN: Pasar self como primer parámetro
                            resultado = self.analyze_chat(config, chat)
                            if resultado['success']:
                                self.stdout.write(
                                    self.style.SUCCESS(f'Chat {chat.IDChat} procesado exitosamente')
                                )
                            else:
                                self.stdout.write(
                                    self.style.WARNING(f'Chat {chat.IDChat} no procesado: {resultado.get("reason")}')
                                )
                                
                            chats_procesados.add(mensaje.IDChat)

                        except Whatsapp.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(f'Chat {mensaje.IDChat} no encontrado')
                            )
                        except WhatsappConfiguracion.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(f'Configuración WhatsApp no encontrada para chat {mensaje.IDChat}')
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'Error procesando chat {mensaje.IDChat}: {str(e)}')
                            )
                            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error procesando mensajes por usuario: {str(e)}')
            )

        self.stdout.write(self.style.SUCCESS('Proceso completado'))
        return "Completado"
    
    def analyze_chat(self, setting, chat):
        """
        CORRECCIÓN: Ahora es un método de instancia con self como primer parámetro
        """
        try:
            # 1. Obtener y formatear mensajes del chat
            msgs = WhatsappMensajes.objects.filter(
                IDChat=chat.IDChat
            ).exclude(
                Telefono=setting.Telefono
            ).order_by('IDChatMensaje')
        
            chat_history = [
                {"content": msg.Mensaje, "role": "user"}
                for msg in msgs if msg.Mensaje
            ]
        
            # 2. Verificar cantidad mínima de mensajes
            if len(chat_history) < setting.envio_lead_n_chat:
                return {'success': False, 'reason': 'insufficient_messages'}
        
            # 3. Analizar chat con IA
            result = analyze_chat_improved(chat_history)
        
            if not result['success']:
                return {'success': False, 'reason': 'analysis_failed', 'error': result.get('error')}
        
            # 4. Validar que AL MENOS UN criterio sea True
            result_ia = result['data']
            
            # Evaluar cada criterio explícitamente (True, False, o None)
            tiene_propiedad = result_ia.get('tiene_propiedad') == True
            propiedad_registrada = result_ia.get('propiedad_en_registros_publicos') == True
            prestamo_suficiente = result_ia.get('prestamo_mayor_20000') == True
            
            # Determinar si es efectivo
            es_efectivo = False
            
            # OPCIÓN A: Es efectivo si cumple los 3 criterios
            if tiene_propiedad and propiedad_registrada and prestamo_suficiente:
                es_efectivo = True
        
            # 5. Preparar y enviar payload
            marca = Marca.objects.filter(id=setting.marca_id).first()
            lead = Lead.objects.filter(id=chat.lead_id).first()
            
            # Validar que la marca existe
            if not marca:
                return {'success': False, 'reason': 'marca_not_found'}
            if not lead:
                return {'success': False, 'reason': 'lead_not_found'}

            payload = {
                'codigo': lead.codigo,
                'marca': marca.nombre.upper(),
                'es_efectivo': es_efectivo
            }
            
            # 6. Enviar a API externa
            response = None  # Inicializar variable response
            try:
                headers = {
                    'Content-Type': 'application/json', 
                    'Accept': 'application/json'
                }
                response = requests.post(
                    f"{settings.API_GI}chat-reasignacion-usuario",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
            
                response_data = response.json()
                data = response_data.get('data')

                # Verificar que data no sea None
                if not data:
                    return {'success': False, 'reason': 'api_response_empty_data'}

                # Actualizar el lead
                try:
                    qs = get_object_or_404(Lead, id=lead.id)
                    serializer = LeadSerializer(qs, data=data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        return {
                            'success': False, 
                            'reason': 'serializer_validation_failed',
                            'errors': serializer.errors
                        }

                    # CORRECCIÓN: Actualizar WhatsapChatUser correctamente
                    chat_user = WhatsapChatUser.objects.filter(IDChat=chat.IDChat).first()
                    if chat_user: 
                        nuevo_user_id = serializer.data.get('usuario_asignado')
                        if nuevo_user_id:  # Verificar que no sea None
                            chat_user.user_id = nuevo_user_id
                            chat_user.save()

                            WhatsapChatUserHistorial.objects.create(
                                whatsapp_chat_user_id=chat_user,
                                IDChat=chat.IDChat,
                                user_id=nuevo_user_id
                            )

                    chat.lead_reasignado = True
                    chat.save()
                    
                    # Push notification
                    try:
                        firebase_service = FirebaseServiceV1()
                        tokens = get_tokens_by_user(nuevo_user_id)
                        if len(tokens) > 0:
                            firebase_service.send_to_multiple_devices(
                                tokens=tokens,
                                title="Nuevo lead recibido en WhatsApp",
                                body=self.simple_message(serializer.data),
                                data={'type': 'router', 'route_name': 'WhatsappPage'}
                            )
                    except Exception as firebase_error:
                        # Log el error pero no fallar el proceso
                        self.stdout.write(
                            self.style.WARNING(f"Error enviando notificación Firebase: {firebase_error}")
                        )
                    
                    return {
                        'success': True,
                        'data': data,
                        'extracted_data': result_ia,
                        'payload_sent': payload
                    }
                    
                except Exception as serializer_error:
                    return {
                        'success': False, 
                        'reason': 'lead_update_failed',
                        'error': str(serializer_error)
                    }
            
            except requests.exceptions.Timeout:
                return {'success': False, 'reason': 'api_timeout'}
            except requests.exceptions.HTTPError as e:
                return {
                    'success': False, 
                    'reason': 'api_http_error', 
                    'error': str(e),
                    'status_code': response.status_code if response else None
                }
            except requests.RequestException as e:
                return {'success': False, 'reason': 'api_send_failed', 'error': str(e)}
            except ValueError as e:  # Para errores de JSON parsing
                return {'success': False, 'reason': 'api_response_invalid', 'error': str(e)}
            
        except Exception as e:
            # Capturar cualquier error no manejado
            return {
                'success': False, 
                'reason': 'unexpected_error',
                'error': str(e)
            }

    def simple_message(self, lead):
        """
        Genera mensaje simple para notificaciones de nuevo lead
        """
        try:
            marca = getattr(lead, 'marca', 'N/A')
            nombre = getattr(lead, 'nombre_lead', 'N/A')
            monto = getattr(lead, 'monto_solicitado', 0)
            celular = getattr(lead, 'celular', 'N/A')
            ocurrencia = getattr(lead, 'ocurrencia', 'N/A')
            
            return (
                f"Nueva Lead de {marca}: Nombre: {nombre}; "
                f"Monto Solicitado: S/. {monto}; "
                f"Celular: {celular}; Ocurrencia: {ocurrencia}."
            )
        except Exception as e:
            return "Nueva Lead recibida"