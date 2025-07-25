from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Q
from ..models import Acceso, AccesoPerfil
from ..serializers import AccesoSerializer, AccesoPerfilSerializer

class AccesosViewSet(viewsets.ViewSet):
   
    def get_access_perfil(self, request, perfil_id=None):
        """
        Obtiene los accesos por perfil (equivalente a getAccessEmpresa)
        """
        try:
            # Join entre AccesoPerfil y Acceso
            accesos_perfil = AccesoPerfil.objects.select_related('acceso_id').filter(
                perfil_id=perfil_id
            )
           
            data = []
            for ap in accesos_perfil:
                data.append({
                    'id': ap.acceso_id.acceso_id,
                    'label': ap.acceso_id.acceso,
                    'icono': ap.acceso_id.icono
                })
           
            return Response({
                'success': True,
                'data': data
            }, status=status.HTTP_200_OK)
           
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_access_tree(self, request):
        """
        Obtiene la estructura jerárquica de accesos (equivalente a getAccess)
        """
        try:
            # Obtener accesos principales (terminan en 000000)
            accesos_principales = Acceso.objects.filter(
                acceso_id__endswith='000000',
                estado=True  # Agregado filtro de estado
            ).order_by('acceso_id')
           
            data = []
            for acceso in accesos_principales:
                item = {
                    'id': acceso.acceso_id,
                    'label': acceso.acceso,
                    'icono': acceso.icono,
                    'children': self.get_child_one(acceso.acceso_id[:2])
                }
                data.append(item)
           
            return Response({
                'success': True,
                'data': data
            }, status=status.HTTP_200_OK)
           
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def store_access_perfil(self, request, perfil_id=None):
        """
        Guarda los accesos para un perfil (equivalente a store)
        """
        try:
            # Eliminar accesos existentes del perfil
            AccesoPerfil.objects.filter(perfil_id=perfil_id).delete()
           
            # Obtener la lista de accesos del request
            access_list = request.data.get('access', [])
           
            # Crear nuevos registros
            for acceso_id in access_list:
                try:
                    acceso = Acceso.objects.get(acceso_id=acceso_id)
                    AccesoPerfil.objects.create(
                        acceso_id=acceso,
                        perfil_id=perfil_id
                    )
                except Acceso.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': f'Acceso {acceso_id} no existe'
                    }, status=status.HTTP_400_BAD_REQUEST)
           
            return Response({
                'success': True,
                'message': 'Acceso guardado con éxito.'
            }, status=status.HTTP_200_OK)
           
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def show_access_perfil(self, request, perfil_id=None):
        """
        Muestra los accesos de un perfil específico (equivalente a show)
        """
        try:
            accesos_perfil = AccesoPerfil.objects.filter(
                perfil_id=perfil_id
            ).values_list('acceso_id__acceso_id', flat=True)
           
            return Response({
                'success': True,
                'data': list(accesos_perfil)
            }, status=status.HTTP_200_OK)
           
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
    def get_child_one(self, prefix):
        """
        Obtiene los hijos de primer nivel
        """
        # Excluir los que terminan en 000000
        principales_ids = Acceso.objects.filter(
            acceso_id__endswith='000000'
        ).values_list('acceso_id', flat=True)
        
        accesos = Acceso.objects.filter(
            acceso_id__startswith=prefix,
            acceso_id__endswith='0000',
            estado=True
        ).exclude(
            acceso_id__in=principales_ids
        ).order_by('acceso_id')
        
        result = []
        for acceso in accesos:
            # Verificar si tiene hijos (buscar accesos que empiecen con los primeros 4 dígitos)
            count_child = Acceso.objects.filter(
                acceso_id__startswith=acceso.acceso_id[:4],
                estado=True
            ).exclude(
                acceso_id__endswith='0000'  # Excluir submódulos
            ).exclude(
                acceso_id=acceso.acceso_id  # Excluir el mismo acceso
            ).count()
            
            if count_child > 0:  # Cambiado de > 1 a > 0
                item = {
                    'id': acceso.acceso_id,
                    'label': acceso.acceso,
                    'icono': acceso.icono,
                    'children': self.get_child_two(acceso.acceso_id)
                }
            else:
                item = {
                    'id': acceso.acceso_id,
                    'label': acceso.acceso,
                    'icono': acceso.icono
                }
            result.append(item)
        
        return result

    def get_child_two(self, acceso_id):
        """
        Obtiene los hijos de segundo nivel
        """
        # Excluir los que terminan en 0000 (submódulos principales)
        exclude_ids = Acceso.objects.filter(
            acceso_id__endswith='0000'
        ).values_list('acceso_id', flat=True)
        
        # Buscar accesos que empiecen con los primeros 4 dígitos del acceso_id
        # y que NO terminen en '0000' (para obtener las funcionalidades específicas)
        accesos = Acceso.objects.filter(
            acceso_id__startswith=acceso_id[:4],  # Por ejemplo: '0402' para WhatsApp
            estado=True
        ).exclude(
            acceso_id__in=exclude_ids  # Excluir submódulos principales
        ).exclude(
            acceso_id=acceso_id  # Excluir el mismo acceso padre
        ).order_by('acceso_id')
        
        result = []
        for acceso in accesos:
            item = {
                'id': acceso.acceso_id,
                'label': acceso.acceso,
                'icono': acceso.icono
            }
            result.append(item)
        
        return result

    def get_child_three(self, children_queryset):
        """
        Obtiene los hijos de tercer nivel
        """
        result = []
        for acceso in children_queryset:
            item = {
                'id': acceso.acceso_id,
                'label': acceso.acceso,
                'icono': acceso.icono
            }
            result.append(item)
       
        return result