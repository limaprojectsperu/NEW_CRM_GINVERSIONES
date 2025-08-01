import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.utils.datetime_func import get_date_time, get_naive_peru_time
from django.test import RequestFactory
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from apps.openai.openai_chatbot import ChatbotService

from apps.whatsapp.views.whatsapp_app import WhatsappSendAPIView
from apps.messenger.views.messenger_app import MessengerSendView
from apps.messenger.models import Messenger, MessengerMensaje, MessengerConfiguracion
from apps.whatsapp.models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes, WhatsapChatUser
from apps.users.models import Users

chatbot = ChatbotService()

class Command(BaseCommand):
    help = 'Responde automáticamente a mensajes que no han sido respondidos en 5 minutos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando proceso de respuesta automática...'))

        # Procesar mensajes de WhatsApp filtrados por usuario
        self.process_whatsapp_messages_by_user()

        # Procesar mensajes de WhatsApp
        self.process_whatsapp_messages()
        
        # Procesar mensajes de Messenger
        self.process_messenger_messages()
        
        self.stdout.write(self.style.SUCCESS('Proceso completado'))
        return "Completado"

    def process_whatsapp_messages(self):
        """Procesa mensajes de WhatsApp que necesitan respuesta automática"""
        try:
            # Buscar configuraciones con respuesta automática habilitada
            configuraciones = WhatsappConfiguracion.objects.filter(
                responder_automaticamente=True,
                Estado=1  # Solo configuraciones activas
            )
            
            for config in configuraciones:
                # Obtener tiempo personalizado de respuesta (por defecto 5 minutos)
                tiempo_ahora = timezone.now()
                minutos_respuesta = config.responder_automaticamente_minutos
                tiempo_minimo_antiguedad = tiempo_ahora - timedelta(minutes=minutos_respuesta)
                tiempo_maximo_antiguedad = tiempo_ahora - timedelta(minutes=30)
                
                # Buscar mensajes de clientes (origen=2) que cumplan los criterios
                mensajes_candidatos = WhatsappMensajes.objects.filter(
                    IDChat__in=Whatsapp.objects.filter(
                        IDRedSocial=config.IDRedSocial,
                        Estado=1
                    ).values_list('IDChat', flat=True),
                    origen=2,  # Mensaje del cliente
                    created_at__lte=tiempo_minimo_antiguedad,
                    created_at__gt=tiempo_maximo_antiguedad
                ).order_by('IDChat', '-created_at')
                
                # Agrupar por chat para verificar si es el último mensaje
                chats_procesados = set()
                
                for mensaje in mensajes_candidatos:
                    if mensaje.IDChat in chats_procesados:
                        continue
                        
                    # Verificar si es el último mensaje del chat
                    ultimo_mensaje = WhatsappMensajes.objects.filter(
                        IDChat=mensaje.IDChat
                    ).order_by('-created_at').first()
                    
                    if ultimo_mensaje and ultimo_mensaje.IDChatMensaje == mensaje.IDChatMensaje:
                        # Es el último mensaje y es del cliente, generar respuesta
                        chat = Whatsapp.objects.get(IDChat=mensaje.IDChat)
                        
                        self.stdout.write(
                            f'Respondiendo automáticamente a WhatsApp chat {chat.IDChat} - {chat.Nombre}'
                        )
                        
                        self.open_ai_response_whatsapp(config, chat)
                        chats_procesados.add(mensaje.IDChat)
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error procesando WhatsApp: {str(e)}')
            )

    def process_whatsapp_messages_by_user(self):
        """Procesa mensajes de WhatsApp filtrando primero por usuarios con respuesta automática habilitada"""
        try:
            # 1. Primero buscar usuarios con respuesta automática habilitada
            usuarios_auto_respuesta = Users.objects.filter(
                responder_automaticamente=True,
                in_estado=1  # Solo usuarios activos
            )

            if not usuarios_auto_respuesta.exists():
                self.stdout.write('No hay usuarios con respuesta automática habilitada')
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
                minutos_respuesta = usuario.responder_automaticamente_minutos
                tiempo_minimo_antiguedad = tiempo_ahora - timedelta(minutes=minutos_respuesta)
                tiempo_maximo_antiguedad = tiempo_ahora - timedelta(minutes=30)

                # 4. Buscar mensajes candidatos de los chats asignados al usuario
                mensajes_candidatos = WhatsappMensajes.objects.filter(
                    IDChat__in=Whatsapp.objects.filter(
                        IDChat__in=chats_usuario,
                        Estado=1  # Solo chats activos
                    ).values_list('IDChat', flat=True),
                    origen=2,  # Mensaje del cliente
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
                        # Es el último mensaje y es del cliente, generar respuesta
                        try:
                            chat = Whatsapp.objects.get(IDChat=mensaje.IDChat)
                            
                            # Obtener la configuración de WhatsApp asociada al chat
                            config = WhatsappConfiguracion.objects.get(
                                IDRedSocial=chat.IDRedSocial,
                                Estado=1
                            )

                            self.stdout.write(
                                f'Respondiendo automáticamente por usuario {usuario.name} '
                                f'a WhatsApp chat {chat.IDChat} - {chat.Nombre}'
                            )

                            # Generar respuesta usando la configuración del chat
                            self.open_ai_response_whatsapp(config, chat)
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
                self.style.ERROR(f'Error procesando mensajes por usuario: {str(e)}')
            )

    def process_messenger_messages(self):
        """Procesa mensajes de Messenger que necesitan respuesta automática"""
        try:
            # Buscar configuraciones con respuesta automática habilitada
            configuraciones = MessengerConfiguracion.objects.filter(
                responder_automaticamente=True,
                Estado=1  # Solo configuraciones activas
            )
            
            for config in configuraciones:
                # Obtener tiempo personalizado de respuesta (por defecto 5 minutos)
                tiempo_ahora = timezone.now()
                minutos_respuesta = config.responder_automaticamente_minutos
                tiempo_minimo_antiguedad = tiempo_ahora - timedelta(minutes=minutos_respuesta)
                tiempo_maximo_antiguedad = tiempo_ahora - timedelta(minutes=30)

                # Buscar mensajes de clientes (origen=2) que cumplan los criterios
                mensajes_candidatos = MessengerMensaje.objects.filter(
                    IDChat__in=Messenger.objects.filter(
                        IDRedSocial=config.IDRedSocial,
                        Estado=1
                    ).values_list('IDChat', flat=True),
                    origen=2,  # Mensaje del cliente
                    created_at__lte=tiempo_minimo_antiguedad,
                    created_at__gt=tiempo_maximo_antiguedad
                ).order_by('IDChat', '-created_at')
                
                # Agrupar por chat para verificar si es el último mensaje
                chats_procesados = set()
                
                for mensaje in mensajes_candidatos:
                    if mensaje.IDChat in chats_procesados:
                        continue
                        
                    # Verificar si es el último mensaje del chat
                    ultimo_mensaje = MessengerMensaje.objects.filter(
                        IDChat=mensaje.IDChat
                    ).order_by('-created_at').first()
                    
                    if ultimo_mensaje and ultimo_mensaje.IDChatMensaje == mensaje.IDChatMensaje:
                        # Es el último mensaje y es del cliente, generar respuesta
                        chat = Messenger.objects.get(IDChat=mensaje.IDChat)
                        
                        self.stdout.write(
                            f'Respondiendo automáticamente a Messenger chat {chat.IDChat} - {chat.Nombre}'
                        )
                        
                        self.open_ai_response_messenger(config, chat)
                        chats_procesados.add(mensaje.IDChat)
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error procesando Messenger: {str(e)}')
            )

    def open_ai_response_whatsapp(self, setting, chat):
        """Genera respuesta usando OpenAI para WhatsApp"""
        try:
            ultimos_mensajes = list(WhatsappMensajes.objects.filter(
                IDChat=chat.IDChat
            ).order_by('-IDChatMensaje')[:10])
            ultimos_mensajes.reverse()
            
            messages = [
                {
                    "role": "assistant" if entry.Telefono == setting.Telefono else "user", 
                    "content": entry.Mensaje
                } 
                for entry in ultimos_mensajes
            ]

            res = chatbot.get_response(setting.marca_id, messages, 2 if setting.marca_id == 1 else 1)
            self.send_message_whatsapp(setting, chat, res, 3)

            chat.respuesta_generada_openai = True
            chat.save()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generando respuesta OpenAI WhatsApp: {str(e)}')
            )

    def open_ai_response_messenger(self, setting, chat):
        """Genera respuesta usando OpenAI para Messenger"""
        try:
            ultimos_mensajes = list(MessengerMensaje.objects.filter(
                IDChat=chat.IDChat
            ).order_by('-IDChatMensaje')[:4])
            ultimos_mensajes.reverse()
            
            messages = []
            
            for entry in ultimos_mensajes:
                role = "assistant" if entry.IDSender == setting.IDSender else "user"
                messages.append({"role": role, "content": entry.Mensaje})
            
            res = chatbot.get_response(setting.marca_id, messages)
            self.send_message_messenger(setting, chat, res, 3)

            chat.respuesta_generada_openai = True
            chat.save()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generando respuesta OpenAI Messenger: {str(e)}')
            )

    def send_message_whatsapp(self, setting, chat, mensaje, origen=1):
        """Envía mensaje usando WhatsappSendAPIView"""
        try:
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
            
            self.stdout.write(f'Mensaje WhatsApp enviado: {response.status_code}')
            return response
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error enviando mensaje WhatsApp: {str(e)}')
            )

    def send_message_messenger(self, setting, chat, mensaje, origen=1):
        """Envía mensaje usando MessengerSendView"""
        try:
            Fecha, Hora = get_date_time()

            message_data = {
                "IDRedSocial": setting.IDRedSocial,
                "tokenHook": setting.TokenHook,  
                "IdRecipient": chat.IDSender,
                "IDChat": chat.IDChat,
                "IDSender": setting.IDSender,
                "Mensaje": mensaje,
                "Fecha": Fecha,
                "Hora": Hora,
                "origen": origen,
            }
            
            factory = RequestFactory()
            django_request = factory.post(
                '/api/messenger-app/send-message/',
                data=json.dumps(message_data),
                content_type='application/json'
            )
            
            drf_request = Request(django_request, parsers=[JSONParser()])
            view = MessengerSendView()
            response = view.post(drf_request)
            
            self.stdout.write(f'Mensaje Messenger enviado: {response.status_code}')
            return response
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error enviando mensaje Messenger: {str(e)}')
            )