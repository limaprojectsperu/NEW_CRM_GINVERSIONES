from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class PostDataPagination:
    """
    Paginación personalizada que lee los parámetros desde request.data (POST)
    en lugar de request.GET. Útil para APIs POST que necesitan paginación.
    """
    def __init__(self, default_page_size=30, max_page_size=100):
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        self.page_size = default_page_size
        self.page = 1
        self.queryset = None
        self.total_count = 0
        self.total_pages = 0

    def paginate_queryset(self, queryset, request, view=None):
        """
        Pagina un queryset basado en los parámetros enviados en request.data
        """
        # Obtener parámetros de paginación desde request.data
        self.page = int(request.data.get('page', 1))
        
        # Permitir override del page_size desde request.data, view, o usar default
        if hasattr(view, 'page_size') and view.page_size:
            self.page_size = view.page_size
        else:
            self.page_size = int(request.data.get('page_size', self.default_page_size))
        
        # Validar que page_size no exceda el máximo
        if self.page_size > self.max_page_size:
            self.page_size = self.max_page_size
            
        # Validar que page sea positivo
        if self.page < 1:
            self.page = 1

        self.queryset = queryset
        self.total_count = queryset.count()
        self.total_pages = (self.total_count + self.page_size - 1) // self.page_size

        # Validar que la página solicitada exista
        if self.page > self.total_pages and self.total_pages > 0:
            self.page = self.total_pages

        # Calcular offset
        offset = (self.page - 1) * self.page_size
        
        # Obtener registros para la página actual
        return queryset[offset:offset + self.page_size]

    def get_paginated_response(self, data):
        """
        Retorna la respuesta paginada con formato similar a post_manual_pagination
        """
        return Response({
            'data': data,
            'pagination': {
                'current_page': self.page,
                'total_pages': self.total_pages,
                'total_count': self.total_count,
                'page_size': self.page_size,
                'has_next': self.page < self.total_pages,
                'has_previous': self.page > 1,
                'next_page': self.page + 1 if self.page < self.total_pages else None,
                'previous_page': self.page - 1 if self.page > 1 else None
            }
        })

    def get_page_info(self):
        """
        Retorna solo la información de paginación sin la respuesta completa
        """
        return {
            'current_page': self.page,
            'total_pages': self.total_pages,
            'total_count': self.total_count,
            'page_size': self.page_size,
            'has_next': self.page < self.total_pages,
            'has_previous': self.page > 1,
            'next_page': self.page + 1 if self.page < self.total_pages else None,
            'previous_page': self.page - 1 if self.page > 1 else None
        }


# Mixin para usar en las vistas
class PostPaginationMixin:
    """
    Mixin que añade paginación a las vistas que usan POST
    """
    pagination_class = PostDataPagination
    page_size = 30

    def get_paginator(self):
        if not hasattr(self, '_paginator'):
            self._paginator = self.pagination_class(default_page_size=self.page_size)
        return self._paginator

    def paginate_queryset(self, queryset, request):
        paginator = self.get_paginator()
        return paginator.paginate_queryset(queryset, request, view=self)

    def get_paginated_response(self, data):
        paginator = self.get_paginator()
        return paginator.get_paginated_response(data)