import json
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from ..models import Lead, WhatsappConfiguracion, Whatsapp, WhatsapChatUser, WhatsapChatUserHistorial, WhatsappMensajes
from ..serializers import LeadSerializer
from apps.redes_sociales.models import Marca
from apps.utils.datetime_func import get_date_time, get_naive_peru_time_delta
from apps.utils.find_states import find_state_id
from django.test import RequestFactory
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from ..views.whatsapp_app import WhatsappSendAPIView
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.utils.tokens_phone import get_tokens_by_user
from apps.users.models import Users
from django.shortcuts import get_object_or_404

class LeadViewSet(viewsets.ViewSet):
    """
    API endpoint for managing Lead records with WhatsApp integration.
    """

    """GET """
    def show(self, request, pk):
        qs = get_object_or_404(Lead, id=pk)
        serializer = LeadSerializer(qs)
        return Response({'data': serializer.data})
    
    def create(self, request):
        """
        POST /api/leads/
        Accepts both single Lead object and array of Lead objects.
        Also creates WhatsApp chat records for each lead.
        """
        data = request.data
        
        # Verificar si es un array o un objeto individual
        is_array = isinstance(data, list)
        
        if is_array:
            return self._create_multiple_leads(data)
        else:
            return self._create_single_lead(data)
    
    def _create_single_lead(self, data):
        """
        Crear un solo Lead con registro de WhatsApp
        """
        try:
            with transaction.atomic():
                # Crear el Lead
                serializer = LeadSerializer(data=data)
                if serializer.is_valid():
                    lead = serializer.save()
                    
                    # Crear registro de WhatsApp
                    whatsapp_result = self._create_whatsapp_record(lead)
                    
                    return Response(
                        {
                            'data': serializer.data,
                            'whatsapp_info': whatsapp_result,
                            'message': 'Lead y registro de WhatsApp creados con éxito.'
                        },
                        status=status.HTTP_201_CREATED
                    )
                else:
                    return Response(
                        {
                            'errors': serializer.errors,
                            'message': 'Error al registrar el Lead.'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except Exception as e:
            return Response(
                {
                    'errors': [f'Error interno: {str(e)}'],
                    'message': 'Error al procesar la solicitud.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_multiple_leads(self, data):
        """
        Crear múltiples Leads con registros de WhatsApp
        """
        if not data:
            return Response(
                {
                    'errors': ['El array no puede estar vacío.'],
                    'message': 'Error en los datos enviados.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar todos los datos antes de crear
        serializers = []
        errors = []
        
        for i, lead_data in enumerate(data):
            serializer = LeadSerializer(data=lead_data)
            if serializer.is_valid():
                serializers.append(serializer)
            else:
                errors.append({
                    'index': i,
                    'errors': serializer.errors,
                    'data': lead_data
                })
        
        # Si hay errores, retornar sin crear nada
        if errors:
            return Response(
                {
                    'errors': errors,
                    'message': f'Se encontraron errores en {len(errors)} de {len(data)} registros.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si todo es válido, crear todos los registros en una transacción
        try:
            with transaction.atomic():
                created_leads = []
                whatsapp_results = []
                
                for serializer in serializers:
                    # Crear Lead
                    lead = serializer.save()
                    created_leads.append(LeadSerializer(lead).data)
                    
                    # Crear registro de WhatsApp
                    whatsapp_result = self._create_whatsapp_record(lead)
                    whatsapp_results.append(whatsapp_result)
                
                return Response(
                    {
                        'data': created_leads,
                        'whatsapp_info': whatsapp_results,
                        'message': f'{len(created_leads)} Leads y registros de WhatsApp creados con éxito.',
                        'count': len(created_leads)
                    },
                    status=status.HTTP_201_CREATED
                )
        
        except Exception as e:
            return Response(
                {
                    'errors': [f'Error al guardar en la base de datos: {str(e)}'],
                    'message': 'Error interno del servidor.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_whatsapp_record(self, lead):
        """
        Crear registro de WhatsApp para un Lead
        """
        try:
            # 1. Obtener IDRedSocial basado en la marca del Lead
            marca = Marca.objects.filter(nombre__iexact=lead.marca).first()
            if not marca:
                marca = Marca.objects.filter(id=1).first()
            
            whatsapp_config = WhatsappConfiguracion.objects.filter(
                marca_id=marca.id,
                Estado=1,
                contactar_leads=True
            ).first()
            
            if not whatsapp_config:
                whatsapp_config = WhatsappConfiguracion.objects.filter(
                    Nombre='Presta Capital',
                    Estado=1
                ).first()
            
            # 2. Verificar si ya existe un chat para este teléfono con este usuario
            existing_chat_user = WhatsapChatUser.objects.filter(
                IDChat__in=Whatsapp.objects.filter(
                    Telefono='51'+lead.celular,
                    IDRedSocial=whatsapp_config.IDRedSocial
                ).values_list('IDChat', flat=True),
                user_id=lead.usuario_asignado
            ).first()
            
            if existing_chat_user:
                # El chat ya existe, obtener el chat
                whatsapp_chat = Whatsapp.objects.get(IDChat=existing_chat_user.IDChat)
                whatsapp_chat.lead_id = lead.id
                whatsapp_chat.save()
                chat_created = False
            else:
                # 3. Crear nuevo registro en Whatsapp
                whatsapp_chat = Whatsapp.objects.create(
                    IDRedSocial=whatsapp_config.IDRedSocial,
                    Nombre=lead.nombre_lead,
                    Telefono='51'+lead.celular,
                    FechaUltimaPlantilla=get_naive_peru_time_delta(days=-2),
                    updated_at=timezone.now(),
                    IDEL=find_state_id(2, whatsapp_config.IDRedSocial, 'PENDIENTE DE LLAMADA'),
                    nuevos_mensajes=1,
                    Estado=1,
                    lead_id=lead.id
                )
                chat_created = True
                
                # 4. Crear registro en WhatsapChatUser
                chat_user = WhatsapChatUser.objects.create(
                    IDChat=whatsapp_chat.IDChat,
                    user_id=lead.usuario_asignado
                )

                WhatsapChatUserHistorial.objects.create(
                    whatsapp_chat_user_id=chat_user,
                    IDChat=whatsapp_chat.IDChat,
                    user_id=lead.usuario_asignado
                )
            
            # 5. Crear mensaje inicial con datos del Lead
            mensaje_contenido = self._generate_lead_message(lead)
            Fecha, Hora = get_date_time()

            whatsapp_mensaje = WhatsappMensajes.objects.create(
                IDChat=whatsapp_chat.IDChat,
                Telefono='51'+lead.celular,
                user_id=lead.usuario_asignado,
                Mensaje=mensaje_contenido,
                Fecha=Fecha,
                Hora=Hora,
                origen=2
            )

            self.send_message(whatsapp_config, whatsapp_chat, 'Plantilla', lead)
            
            # Push notification
            firebase_service = FirebaseServiceV1()
            tokens = get_tokens_by_user(lead.usuario_asignado)
            if len(tokens) > 0:
                firebase_service.send_to_multiple_devices(
                    tokens=tokens,
                    title="Nuevo lead recibido en WhatsApp",
                    body= self.simple_message(lead),
                    data={'type': 'router', 'route_name': 'WhatsappPage'}
                )

            return {
                'status': 'success',
                'whatsapp_chat_id': whatsapp_chat.IDChat,
                'chat_created': chat_created,
                'message_id': whatsapp_mensaje.IDChatMensaje,
                'config_id': whatsapp_config.IDRedSocial,
                'marca': lead.marca
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error al crear registro de WhatsApp: {str(e)}'
            }
    
    def send_message(self, setting, chat, mensaje, lead, origen=1):
        """
        Envía mensaje usando WhatsappSendAPIView
        """
        user = Users.objects.filter(co_usuario=lead.usuario_asignado).first()
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
            "message_24_hours": False,
            "template_params_1": lead.nombre_lead,
            "template_params_2": user.name if user and user.name else setting.Nombre,
        }
        
        factory = RequestFactory()
        django_request = factory.post(
            '/api/messenger-app/send-message/',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        drf_request = Request(django_request, parsers=[JSONParser()])
        view = WhatsappSendAPIView()
        return view.post(drf_request)
    
    def simple_message(self, lead):
        f"Nueva Lead de {lead.marca}: Nombre: {lead.nombre_lead}; Monto Solicitado: S/. {lead.monto_solicitado}; "
        f"Celular: {lead.celular}; Ocurrencia: {lead.ocurrencia}."
        
    def _generate_lead_message(self, lead):
        """
        Generar mensaje inicial basado en los datos del Lead
        """
        def split_and_truncate(text, first_max=42, second_max=40):
            if not text:
                return ["", ""]
            part1 = text[:first_max]
            part2 = text[first_max:]
            if len(part2) > second_max:
                part2 = part2[:second_max] + "..."
            return [part1, part2] if part2 else [part1]

        medio_parts = split_and_truncate(lead.medio_captacion)
    
        #📱 Celular: {lead.celular} #debajo del nombre
        mensaje = f"""🆕 NUEVO LEAD REGISTRADO

    👤 Nombre: {lead.nombre_lead}
    🏢 Marca: {lead.marca}
    💰 Monto Solicitado: S/. {lead.monto_solicitado}

    📋 DETALLES:
    • Código solicitud: {lead.codigo_solicitud}
    • Medio de Captación: 
    {medio_parts[0]}""" 

        if len(medio_parts) > 1 and medio_parts[1]:
            mensaje += f"""
    {medio_parts[1]}""" 

        mensaje += f"""
    • Condición: {lead.condicion}
    • Tipo de Garantía: {lead.tipo_garantia}

    📍 UBICACIÓN:
    • Departamento: {lead.departamento}
    • Provincia: {lead.provincia}
    • Distrito: {lead.distrito}

    🏠 Propiedad en RRPP: {'✅ Sí' if lead.propiedad_registros_publicos else '❌ No'}

    📅 Fecha de Registro: {lead.fecha_registro.strftime('%d/%m/%Y %H:%M') if lead.fecha_registro else 'No especificada'}
    📅 Fecha de Asignación: {lead.fecha_asignacion.strftime('%d/%m/%Y %H:%M') if lead.fecha_asignacion else 'No especificada'}

    🔄 Ocurrencia: {lead.ocurrencia}"""

        return mensaje[:2000] # Limitar a 2000 caracteres según el modelo