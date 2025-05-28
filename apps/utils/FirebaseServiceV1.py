import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from django.conf import settings
import os


class FirebaseServiceV1:
    def __init__(self):
        self.project_id = "grupo-imagen-notificaciones"
        self.fcm_url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}"
        self.access_token = None
        self._initialize_access_token()

    def _initialize_access_token(self):
        """
        Inicializar el token de acceso usando la cuenta de servicio
        """
        try:
            # Ruta al archivo de credenciales (ajustar según tu estructura de Django)
            credentials_path = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
            
            # Crear credenciales desde el archivo JSON
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/firebase.messaging']
            )
            
            # Obtener el token de acceso
            credentials.refresh(Request())
            self.access_token = credentials.token
            
        except Exception as e:
            raise Exception(f"Error al inicializar token de acceso: {str(e)}")

    def send_to_device(self, token, title, body, data=None):
        """
        Enviar notificación a un dispositivo específico
        """
        message = {
            'message': {
                'token': token,
                'notification': {
                    'title': title,
                    'body': body
                },
                'android': {
                    'priority': 'high',
                    'notification': {
                        'sound': 'default'
                    }
                },
                'apns': {
                    'payload': {
                        'aps': {
                            'sound': 'default'
                        }
                    }
                }
            }
        }

        if data:
            message['message']['data'] = data

        try:
            response = self._send_notification(message)

            if 'error' in response:
                if (response['error']['code'] == 404 or 
                    'InvalidToken' in response['error']['message']):
                    return {
                        'error': 'Token no encontrado o inválido', 
                        'token': token
                    }
            
            return response
            
        except Exception as e:
            return {'error': str(e)}

    def send_to_multiple_devices(self, tokens, title, body, data=None):
        """
        Enviar notificación a múltiples dispositivos
        """
        responses = {
            'success': [],
            'failed': []
        }

        for token in tokens:
            response = self.send_to_device(token, title, body, data)

            if 'error' in response:
                responses['failed'].append({
                    'token': token,
                    'error': response['error']
                })
            else:
                responses['success'].append({
                    'token': token,
                    'response': response
                })

        return responses

    def send_to_android(self, title, body, data=None):
        """
        Enviar notificación a todos los dispositivos Android
        """
        message = {
            'message': {
                'condition': "'android' in topics",
                'notification': {
                    'title': title,
                    'body': body
                },
                'android': {
                    'priority': 'high',
                    'notification': {
                        'sound': 'default',
                        'default_sound': True,
                        'default_vibrate_timings': True,
                        'notification_priority': 'PRIORITY_HIGH'
                    }
                }
            }
        }

        if data:
            message['message']['data'] = data

        return self._send_notification(message)

    def send_to_ios(self, title, body, data=None):
        """
        Enviar notificación a todos los dispositivos iOS
        """
        message = {
            'message': {
                'condition': "'ios' in topics",
                'notification': {
                    'title': title,
                    'body': body
                },
                'apns': {
                    'payload': {
                        'aps': {
                            'sound': 'default',
                            'content-available': 1,
                            'priority': 10,
                            'badge': 1
                        }
                    }
                }
            }
        }

        if data:
            message['message']['data'] = data

        return self._send_notification(message)

    def send_to_all(self, title, body, data=None):
        """
        Enviar notificación a todos los dispositivos (Android e iOS)
        """
        android_response = self.send_to_android(title, body, data)
        ios_response = self.send_to_ios(title, body, data)

        return {
            'android': android_response,
            'ios': ios_response
        }

    def send_to_topic(self, topic, title, body, data=None):
        """
        Enviar notificación a un tema
        topic: topic-cetpro_id
        """
        message = {
            'message': {
                'topic': topic,
                'notification': {
                    'title': title,
                    'body': body
                },
                'android': {
                    'priority': 'high',
                    'notification': {
                        'sound': 'default',
                        'default_sound': True,
                        'default_vibrate_timings': True,
                        'notification_priority': 'PRIORITY_HIGH'
                    }
                },
                'apns': {
                    'payload': {
                        'aps': {
                            'sound': 'default',
                            'content-available': 1,
                            'priority': 10,
                            'badge': 1
                        }
                    }
                }
            }
        }

        if data:
            message['message']['data'] = data

        return self._send_notification(message)

    def _send_notification(self, message):
        """
        Enviar la notificación usando la API v1
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

        response = requests.post(
            f"{self.fcm_url}/messages:send",
            headers=headers,
            json=message
        )

        return response.json()


# Ejemplo de uso en una vista de Django
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["POST"])
def send_push_notification(request):
    """
    Vista de ejemplo para enviar notificaciones push
    """
    try:
        data = json.loads(request.body)
        
        firebase_service = FirebaseServiceV1()
        
        # Ejemplo de uso según el tipo de notificación
        notification_type = data.get('type', 'device')
        title = data.get('title', '')
        body = data.get('body', '')
        extra_data = data.get('data', None)
        
        if notification_type == 'device':
            token = data.get('token')
            result = firebase_service.send_to_device(token, title, body, extra_data)
            
        elif notification_type == 'multiple':
            tokens = data.get('tokens', [])
            result = firebase_service.send_to_multiple_devices(tokens, title, body, extra_data)
            
        elif notification_type == 'android':
            result = firebase_service.send_to_android(title, body, extra_data)
            
        elif notification_type == 'ios':
            result = firebase_service.send_to_ios(title, body, extra_data)
            
        elif notification_type == 'all':
            result = firebase_service.send_to_all(title, body, extra_data)
            
        elif notification_type == 'topic':
            topic = data.get('topic')
            result = firebase_service.send_to_topic(topic, title, body, extra_data)
            
        else:
            return JsonResponse({'error': 'Tipo de notificación no válido'}, status=400)
        
        return JsonResponse({'success': True, 'result': result})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)