from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from ..models import Lead
from ..serializers import LeadSerializer


class LeadViewSet(viewsets.ViewSet):
    """
    API endpoint for managing Lead records.
    """

    def create(self, request):
        """
        POST /api/leads/
        Accepts both single Lead object and array of Lead objects.
        
        Single Lead example:
        {
            "nombre_lead": "Juan Pérez",
            "celular": "987654321",
            "monto_solicitado": 50000.00
        }
        
        Array of Leads example:
        [
            {
                "nombre_lead": "Juan Pérez",
                "celular": "987654321",
                "monto_solicitado": 50000.00
            },
            {
                "nombre_lead": "María González",
                "celular": "987654322",
                "monto_solicitado": 75000.00
            }
        ]
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
        Crear un solo Lead
        """
        serializer = LeadSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'data': serializer.data,
                    'message': 'Lead registrado con éxito.'
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
    
    def _create_multiple_leads(self, data):
        """
        Crear múltiples Leads
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
                for serializer in serializers:
                    lead = serializer.save()
                    created_leads.append(LeadSerializer(lead).data)
                
                return Response(
                    {
                        'data': created_leads,
                        'message': f'{len(created_leads)} Leads registrados con éxito.',
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