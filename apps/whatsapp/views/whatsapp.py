import os
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.utils.datetime_func import get_naive_peru_time, get_naive_peru_time_delta
from ..models import Whatsapp, WhatsappMensajes, ChatNiveles, WhatsapChatUser
from ..serializers import WhatsappSerializer, WhatsappSingleSerializer, WhatsappAgendaSerializer, WhatsappMensajesSerializer
from apps.utils.find_states import find_state_id
from apps.users.views.wasabi import upload_to_wasabi
from apps.utils.pagination import PostDataPagination
from datetime import datetime, time

class WhatsappListAll(APIView):
    """ GET /api/whatsapp/all/ """
    def get(self, request,  id):
        qs = Whatsapp.objects.filter(IDRedSocial=id, Estado=1)
        data = WhatsappSingleSerializer(qs, many=True).data
        return Response({'data': data})

class WhatsappList(APIView):
    """
    POST /api/whatsapp/all/{id}/?IDEL=&IDSubEstadoLead=&IDNivel=
    """
    def post(self, request, id):
        IDEL           = int(request.data.get('IDEL', -1))
        IDSubEstado    = int(request.data.get('IDSubEstadoLead', -1))
        IDNivel        = int(request.data.get('IDNivel', -1))
        search_text = request.data.get('searchMessage', '').strip()
        user_id = request.data.get('user_id', -1) # Si no tiene el ID, se puede ver todo los chats

        qs = Whatsapp.objects.filter(IDRedSocial=id, Estado=1)

        if IDEL > 0:
            qs = qs.filter(IDEL=IDEL)
        if IDSubEstado > 0:
            qs = qs.filter(IDSubEstadoLead=IDSubEstado)
        if IDNivel > 0:
            # unimos con la tabla chat_niveles
            chat_ids = ChatNiveles.objects.filter(IDNivel=IDNivel).values_list('IDChat', flat=True)
            qs = qs.filter(IDChat__in=chat_ids)

        if user_id > 0:
            # Get all IDChat values associated with the given user_id from WhatsapChatUser
            chat_ids_for_user = WhatsapChatUser.objects.filter(user_id=user_id).values_list('IDChat', flat=True)
            # Filter the main queryset using these chat IDs
            qs = qs.filter(IDChat__in=chat_ids_for_user)

        if search_text:
            matching_messages = WhatsappMensajes.objects.filter(
                Mensaje__icontains=search_text
            ).values_list('IDChat', flat=True).distinct()
            
            qs = qs.filter(IDChat__in=matching_messages)

        qs = qs.order_by('-updated_at')

        # Paginacion
        paginator = PostDataPagination(default_page_size=20)
        paginated_qs = paginator.paginate_queryset(qs, request, view=self)
        serializer = WhatsappSerializer(paginated_qs, many=True)
        
        return paginator.get_paginated_response(serializer.data)

class WhatsappAgendaList(APIView):
    """ POST /api/whatsapp/agenda/ """
    def post(self, request,  id):
        user_id = request.data.get('user_id', -1) # Si no tiene el ID, se puede ver todo los chats

        start_obj = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
        end_obj = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
        start_datetime = datetime.combine(start_obj, time.min)
        end_datetime = datetime.combine(end_obj, time.max)
        
        qs = Whatsapp.objects.filter(IDRedSocial=id, Estado=1)
        qs = qs.filter(fecha_agenda__range=[start_datetime, end_datetime])
        
        if user_id > 0:
            # Get all IDChat values associated with the given user_id from WhatsapChatUser
            chat_ids_for_user = WhatsapChatUser.objects.filter(user_id=user_id).values_list('IDChat', flat=True)
            # Filter the main queryset using these chat IDs
            qs = qs.filter(IDChat__in=chat_ids_for_user)

        data = WhatsappAgendaSerializer(qs, many=True).data
        return Response({'data': data})

class WhatsappNextTemplateList(APIView):
    """ POST /api/whatsapp/next-template/ """
    def post(self, request,  id):
        user_id = request.data.get('user_id', -1) # Si no tiene el ID, se puede ver todo los chats

        start_obj = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
        end_obj = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
        start_datetime = datetime.combine(start_obj, time.min)
        end_datetime = datetime.combine(end_obj, time.max)
        
        qs = Whatsapp.objects.filter(IDRedSocial=id, Estado=1)
        qs = qs.filter(fecha_proxima_plantilla__range=[start_datetime, end_datetime])
        
        if user_id > 0:
            # Get all IDChat values associated with the given user_id from WhatsapChatUser
            chat_ids_for_user = WhatsapChatUser.objects.filter(user_id=user_id).values_list('IDChat', flat=True)
            # Filter the main queryset using these chat IDs
            qs = qs.filter(IDChat__in=chat_ids_for_user)

        data = WhatsappAgendaSerializer(qs, many=True).data
        return Response({'data': data})
    
class WhatsappStore(APIView):
    """ POST /api/whatsapp/store/ """
    def post(self, request):
        new_date = get_naive_peru_time()
        w = Whatsapp.objects.create(
            IDRedSocial = request.data['IDRedSocial'],
            Nombre      = request.data['Nombre'],
            Telefono    = request.data['Telefono'],
            Estado      = 1,
            updated_at  = new_date,
            FechaUltimaPlantilla = get_naive_peru_time_delta(days=-2),
        )
        return Response({'message': 'Nuevo Chat registrado correctamente.', 'data': WhatsappSerializer(w).data})

class WhatsappShow(APIView):
    """ GET /api/whatsapp/message/{id}/ """
    def get(self, request, id):
        msgs = WhatsappMensajes.objects.filter(IDChat=id).order_by('IDChatMensaje')
        # marcar como vistos
        WhatsappMensajes.objects.filter(IDChat=id, Estado=2).update(Estado=3)
        # reset new count
        chat = Whatsapp.objects.filter(IDChat=id).first()
        if chat:
            chat.nuevos_mensajes = 0
            chat.save()

        data = WhatsappMensajesSerializer(msgs, many=True).data
        return Response({'data': data})
    
class WhatsappUpdateLead(APIView):
    """
    POST /api/whatsapp/update-lead/{id}/
    """
    def post(self, request, id):
        payload = request.data
        IDEL = payload.get('IDEL', {}).get('IDEL')
        IDSub = payload.get('IDSubEstadoLead', {}).get('IDSubEstadoLead') if payload.get('IDSubEstadoLead') else None
        
        Whatsapp.objects.filter(IDChat=payload.get('IDChat')).update(
            IDEL=IDEL,
            IDSubEstadoLead=IDSub
        )
        return Response({'message': 'Estado actualizado con éxito.'})

class WhatsappUpdate(APIView):
    """ POST /api/whatsapp/update-chat/{id}/ """
    def post(self, request, id):
        # actualizar nombre
        Whatsapp.objects.filter(IDChat=id).update(Nombre=request.data.get('Nombre'))

        avatar_url = None
        upload = request.FILES.get('file')
        if upload:
            # Generar nombre de archivo usando timestamp
            extension = os.path.splitext(upload.name)[1]  # Obtener extensión
            filename = f'{int(timezone.now().timestamp())}{extension}'
                
            # Definir la ruta en Wasabi
            file_path = f'media/whatsapp/avatars/{filename}'
                
            # Subir archivo a Wasabi usando la función auxiliar
            saved_path = upload_to_wasabi(upload, file_path)

            # Generar URL para acceder al archivo
            avatar_url= f"/{file_path}"

            Whatsapp.objects.filter(IDChat=id).update(Avatar=avatar_url)

        return Response({'message': 'Perfil actualizado con éxito.', 'data': avatar_url})

class WhatsappUpdateDate(APIView):
    """ POST /api/whatsapp/update-date/{id}/ """
    def post(self, request, id):
        Whatsapp.objects.filter(IDChat=id).update(updated_at=get_naive_peru_time())
        return Response({'message': 'ok'})

class WhatsappUpdateOpenai(APIView):
    """ POST /api/whatsapp/update-openai/{id}/ """
    def post(self, request, id):
        Whatsapp.objects.filter(IDChat=id).update(openai=request.data.get('openai'))
        return Response({'message': 'ok'})

class WhatsappUpdateGeneratedResponse(APIView):
    """ POST /api/whatsapp/generated-response/{id}/ """
    def post(self, request, id):
        Whatsapp.objects.filter(IDChat=id).update(respuesta_generada_openai=request.data.get('respuesta_generada_openai'))
        return Response({'message': 'ok'})

class WhatsappUpdateAgenda(APIView):
    """ PUT /api/whatsapp/generated-response/{id}/ """
    def put(self, request, id):
        Whatsapp.objects.filter(IDChat=id).update(
            fecha_agenda=request.data.get('fecha_agenda'),
            user_id_agenda=request.data.get('user_id_agenda'),
            )
        return Response({'message': 'Agenda guardada con éxito.'})

class WhatsappUpdateNextTemplate(APIView):
    """ PUT /api/whatsapp/generated-response/{id}/ """
    def put(self, request, id):
        Whatsapp.objects.filter(IDChat=id).update(
            fecha_proxima_plantilla=request.data.get('fecha_proxima_plantilla'),
            user_id_proxima_plantilla=request.data.get('user_id_proxima_plantilla'),
            template_name=request.data.get('template_name'),
            template_params=request.data.get('template_params'),
            )
        return Response({'message': 'Plantilla programada con éxito.'})

class WhatsappDestroy(APIView):
    """ POST /api/whatsapp/delete/{id}/ """
    def post(self, request, id):
        Whatsapp.objects.filter(IDChat=id).update(Estado=0)
        return Response({'message': 'ok'})
