import os
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.utils.datetime_func import get_naive_peru_time
from ..models import Whatsapp, WhatsappMensajes, ChatNiveles, WhatsappConfiguracion
from ..serializers import WhatsappSerializer, WhatsappSingleSerializer, WhatsappMensajesSerializer, WhatsappConfiguracionSerializer
from apps.utils.find_states import find_state_id
from apps.users.views.wasabi import upload_to_wasabi

class WhatsappListAll(APIView):
    """ GET /api/whatsapp/all/ """
    def get(self, request):
        qs = Whatsapp.objects.filter(Estado=1)
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

        qs = Whatsapp.objects.filter(IDRedSocial=id, Estado=1)

        if IDEL > 0:
            qs = qs.filter(IDEL=IDEL)
        if IDSubEstado > 0:
            qs = qs.filter(IDSubEstadoLead=IDSubEstado)
        if IDNivel > 0:
            # unimos con la tabla chat_niveles
            chat_ids = ChatNiveles.objects.filter(IDNivel=IDNivel).values_list('IDChat', flat=True)
            qs = qs.filter(IDChat__in=chat_ids)

        if search_text:
            matching_messages = WhatsappMensajes.objects.filter(
                Mensaje__icontains=search_text
            ).values_list('IDChat', flat=True).distinct()
            
            qs = qs.filter(IDChat__in=matching_messages)

        qs = qs.order_by('-updated_at')
        data = WhatsappSerializer(qs, many=True).data
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
            FechaUltimaPlantilla = new_date
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
            if chat.IDEL == find_state_id(2, 'No leído'):
                chat.IDEL = find_state_id(2, 'Leído')
            chat.save()

        data = WhatsappMensajesSerializer(msgs, many=True).data
        return Response({'data': data})
    
class WhatsappSettingList(APIView):
    """
    GET /api/whatsapp/setting/
    """
    def get(self, request):
        qs = WhatsappConfiguracion.objects.filter(Estado=1)
        serializer = WhatsappConfiguracionSerializer(qs, many=True)
        return Response({'data': serializer.data})

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

class WhatsappDestroy(APIView):
    """ POST /api/whatsapp/delete/{id}/ """
    def post(self, request, id):
        Whatsapp.objects.filter(IDChat=id).update(Estado=0)
        return Response({'message': 'ok'})
