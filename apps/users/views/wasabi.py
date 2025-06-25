import boto3
import mimetypes
import os
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.views import View
from django.core.files.storage import default_storage
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

class WasabiFileHandler(View):
    """
    Maneja archivos almacenados en Wasabi S3
    Similar al WasabiController de Laravel
    """
    
    def __init__(self):
        super().__init__()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.WASABI_ACCESS_KEY_ID,
            aws_secret_access_key=settings.WASABI_SECRET_ACCESS_KEY,
            endpoint_url=settings.WASABI_ENDPOINT_URL,
            region_name=settings.WASABI_DEFAULT_REGION
        )
    
    def get(self, request, path, path2=None, path3=None, path4=None, file=None, action='view'):
        """
        Maneja tanto la visualización directa como URLs pre-firmadas
        Soporta hasta 4 niveles de directorios más el nombre de archivo
        """
        # Construir la ruta del archivo
        file_path = self._build_file_path(path, path2, path3, path4, file)
        
        # Verificar si el archivo existe
        if not self._file_exists(file_path):
            raise Http404("El archivo no existe")
        
        # Determinar acción basada en parámetros o tipo de archivo
        if action == 'redirect' or request.GET.get('redirect') == '1':
            return self._get_presigned_url(file_path)
        else:
            return self._serve_file_directly(file_path)
    
    def _build_file_path(self, path, path2=None, path3=None, path4=None, file=None):
        """Construye la ruta completa del archivo con hasta 4 niveles de directorio"""
        parts = [path]
        if path2:
            parts.append(path2)
        if path3:
            parts.append(path3)
        if path4:
            parts.append(path4)
        if file:
            parts.append(file)
        return '/'.join(parts)
    
    def _file_exists(self, file_path):
        """Verifica si el archivo existe en Wasabi"""
        try:
            self.s3_client.head_object(
                Bucket=settings.WASABI_BUCKET,
                Key=file_path
            )
            return True
        except ClientError:
            return False
    
    @method_decorator(cache_control(max_age=3600))
    def _serve_file_directly(self, file_path):
        """Sirve el archivo directamente a través de Django"""
        try:
            # Obtener el archivo desde Wasabi
            response = self.s3_client.get_object(
                Bucket=settings.WASABI_BUCKET,
                Key=file_path
            )
            
            # Leer el contenido
            file_content = response['Body'].read()
            
            # Determinar el tipo MIME
            content_type = response.get('ContentType')
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Crear respuesta HTTP
            http_response = HttpResponse(
                file_content,
                content_type=content_type
            )
            
            # Agregar headers adicionales para mejor manejo del navegador
            file_name = file_path.split('/')[-1]
            
            # Para PDFs y otros documentos, mostrar en línea
            if content_type == 'application/pdf':
                http_response['Content-Disposition'] = f'inline; filename="{file_name}"'
            # Para imágenes, mostrar en línea
            elif content_type.startswith('image/'):
                http_response['Content-Disposition'] = f'inline; filename="{file_name}"'
            else:
                # Para otros archivos, forzar descarga
                http_response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            
            # Cache headers
            http_response['Cache-Control'] = 'max-age=3600'
            
            return http_response
            
        except ClientError as e:
            raise Http404("Error al acceder al archivo")
    
    def _get_presigned_url(self, file_path):
        """Genera una URL pre-firmada y redirige"""
        try:
            # Generar URL pre-firmada válida por 60 minutos
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.WASABI_BUCKET,
                    'Key': file_path
                },
                ExpiresIn=3600  # 60 minutos
            )
            
            return HttpResponseRedirect(presigned_url)
            
        except ClientError as e:
            raise Http404("Error al generar URL del archivo")


class WasabiFileUpload(View):
    """
    Maneja la subida de archivos a Wasabi
    """
    
    def post(self, request):
        """Sube archivos a Wasabi"""
        if 'file' not in request.FILES:
            return HttpResponse('No se proporcionó archivo', status=400)
        
        file = request.FILES['file']
        file_path = request.POST.get('path', '')
        
        # Si se proporciona una ruta personalizada
        if file_path:
            full_path = f"{file_path}/{file.name}"
        else:
            # Usar estructura de fecha por defecto
            now = datetime.now()
            full_path = f"uploads/{now.year}/{now.month:02d}/{now.day:02d}/{file.name}"
        
        try:
            # Subir usando django-storages
            saved_path = default_storage.save(full_path, file)
            
            return HttpResponse(f'Archivo subido exitosamente: {saved_path}', status=200)
            
        except Exception as e:
            return HttpResponse(f'Error al subir archivo: {str(e)}', status=500)


# Función auxiliar para uso en otros controladores/vistas
def upload_to_wasabi(file, file_path):
    """
    Función auxiliar para subir archivos desde otros lugares del código
    Similar a Storage::disk('wasabi')->put() de Laravel
    """
    try:
        if hasattr(file, 'read'):
            # Es un archivo
            saved_path = default_storage.save(file_path, file)
        else:
            # Es contenido (string/bytes)
            from django.core.files.base import ContentFile
            content_file = ContentFile(file)
            saved_path = default_storage.save(file_path, content_file)
        
        return saved_path
    except Exception as e:
        raise Exception(f"Error al subir archivo a Wasabi: {str(e)}")

def get_wasabi_file_url(file_path, expires_in=3600):
    """
    Genera una URL pre-firmada para un archivo en Wasabi
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.WASABI_ACCESS_KEY_ID,
        aws_secret_access_key=settings.WASABI_SECRET_ACCESS_KEY,
        endpoint_url=settings.WASABI_ENDPOINT_URL,
        region_name=settings.WASABI_DEFAULT_REGION
    )
    
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.WASABI_BUCKET,
                'Key': file_path
            },
            ExpiresIn=expires_in
        )
        return url
    except ClientError:
        return None

# Para los chats

def save_file_to_wasabi(file_data, file_path, content_type=None):
    """
    Guarda un archivo en Wasabi.
    
    Args:
        file_data: Datos del archivo (bytes o file-like object)
        file_path (str): Ruta donde guardar el archivo en Wasabi
        content_type (str, optional): Tipo MIME del archivo
    
    Returns:
        dict: Resultado de la operación
              - success (bool): True si se guardó correctamente
              - file_path (str): Ruta del archivo guardado
              - error (str): Mensaje de error si success=False
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.WASABI_ACCESS_KEY_ID,
            aws_secret_access_key=settings.WASABI_SECRET_ACCESS_KEY,
            endpoint_url=settings.WASABI_ENDPOINT_URL,
            region_name=settings.WASABI_DEFAULT_REGION
        )
        
        # Preparar argumentos para la subida
        put_args = {
            'Bucket': settings.WASABI_BUCKET,
            'Key': file_path,
            'Body': file_data
        }
        
        if content_type:
            put_args['ContentType'] = content_type
        
        # Subir archivo a Wasabi
        s3_client.put_object(**put_args)
        
        return {
            'success': True,
            'file_path': file_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'file_path': file_path,
            'error': f'Error guardando archivo en Wasabi: {str(e)}'
        }

def get_wasabi_file_data(url_file):
    """
    Obtiene los datos de un archivo desde Wasabi o almacenamiento local.
    
    Args:
        url_file (str): URL del archivo (puede ser /wasabi/path, /media/path, o path directo)
    
    Returns:
        dict: Diccionario con los datos del archivo o información de error
              - success (bool): True si se obtuvo el archivo correctamente
              - file_data (bytes): Contenido del archivo si success=True
              - filename (str): Nombre del archivo si success=True
              - content_type (str): Tipo MIME del archivo si success=True
              - error (str): Mensaje de error si success=False
              - file_path (str): Ruta procesada del archivo
              - source (str): 'wasabi' o 'local' para indicar la fuente
    """
    try:
        # Determinar content_type basado en la extensión
        def get_content_type(file_path):
            content_type_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp',
                '.mp4': 'video/mp4', '.avi': 'video/avi', '.mov': 'video/quicktime',
                '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.json': 'application/json',
                '.zip': 'application/zip',
                '.rar': 'application/x-rar-compressed'
            }
            file_extension = os.path.splitext(file_path)[1].lower()
            return content_type_map.get(file_extension, 'application/octet-stream')

        # Intentar primero con Wasabi
        try:
            # Extraer el file_path de la URL para Wasabi
            if url_file.startswith('/wasabi/'):
                file_path = url_file[8:]  # Remover "/wasabi/" del inicio
            elif url_file.startswith('/media/'):
                file_path = url_file[1:]  # Remover "/" del inicio, mantener "media/"
            elif url_file.startswith('media/'):
                file_path = url_file  # Ya está en formato correcto
            else:
                # Si viene en otro formato, asumir que es la ruta completa
                file_path = url_file.lstrip('/')
            
            # Crear cliente S3 para Wasabi
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.WASABI_ACCESS_KEY_ID,
                aws_secret_access_key=settings.WASABI_SECRET_ACCESS_KEY,
                endpoint_url=settings.WASABI_ENDPOINT_URL,
                region_name=settings.WASABI_DEFAULT_REGION
            )
            
            # Verificar si el archivo existe en Wasabi
            s3_client.head_object(
                Bucket=settings.WASABI_BUCKET,
                Key=file_path
            )
            
            # Descargar archivo desde Wasabi
            response = s3_client.get_object(
                Bucket=settings.WASABI_BUCKET,
                Key=file_path
            )
            file_data = response['Body'].read()
            
            # Obtener información del archivo
            filename = os.path.basename(file_path)
            content_type = response.get('ContentType') or get_content_type(file_path)
            
            return {
                'success': True,
                'file_data': file_data,
                'filename': filename,
                'content_type': content_type,
                'file_path': file_path,
                'source': 'wasabi'
            }
            
        except ClientError:
            # Si no está en Wasabi, intentar con almacenamiento local
            pass
        
        # Intentar con almacenamiento local
        if os.path.isabs(url_file):
            local_file_path = url_file
        else:
            clean_path = url_file.lstrip('/')
            local_file_path = os.path.join(settings.MEDIA_ROOT, clean_path)
        
        # Normalizar la ruta
        local_file_path = os.path.normpath(local_file_path)
        
        if os.path.exists(local_file_path):
            # Leer archivo desde disco local
            with open(local_file_path, 'rb') as f:
                file_data = f.read()
            
            filename = os.path.basename(local_file_path)
            content_type = get_content_type(local_file_path)
            
            return {
                'success': True,
                'file_data': file_data,
                'filename': filename,
                'content_type': content_type,
                'file_path': local_file_path,
                'source': 'local'
            }
        
        # Si no se encuentra en ningún lado
        return {
            'success': False,
            'error': f'Archivo no encontrado en Wasabi ni en almacenamiento local: {url_file}',
            'file_path': url_file,
            'source': 'none'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error procesando archivo: {str(e)}',
            'file_path': url_file,
            'source': 'error'
        }

def check_wasabi_file_exists(url_file):
    """
    Verifica si un archivo existe en Wasabi.
    
    Args:
        url_file (str): URL del archivo
    
    Returns:
        bool: True si el archivo existe, False en caso contrario
    """
    try:
        # Extraer el file_path de la URL
        if url_file.startswith('/wasabi/'):
            file_path = url_file[8:]
        elif url_file.startswith('/media/'):
            file_path = url_file[1:]
        elif url_file.startswith('media/'):
            file_path = url_file
        else:
            file_path = url_file.lstrip('/')
        
        # Crear cliente S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.WASABI_ACCESS_KEY_ID,
            aws_secret_access_key=settings.WASABI_SECRET_ACCESS_KEY,
            endpoint_url=settings.WASABI_ENDPOINT_URL,
            region_name=settings.WASABI_DEFAULT_REGION
        )
        
        # Verificar existencia
        s3_client.head_object(
            Bucket=settings.WASABI_BUCKET,
            Key=file_path
        )
        return True
        
    except ClientError:
        return False
    except Exception:
        return False