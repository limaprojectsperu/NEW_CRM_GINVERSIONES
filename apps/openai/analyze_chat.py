import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

class ChatAnalyzerView(View):
    def __init__(self):
        super().__init__()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        try:
            # Parsear datos del request
            data = json.loads(request.body)
            prompt = data.get('prompt', '')
            
            if not prompt:
                return JsonResponse({
                    'error': 'El prompt es requerido'
                }, status=400)
            
            # Llamada a OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto analizador de conversaciones. Extrae información específica del chat de manera precisa y estructurada."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=250
            )
            
            result = response.choices[0].message.content
            
            return JsonResponse({
                'success': True,
                'result': result,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON inválido en el request'
            }, status=400)
            
        except Exception as e:
            logger.error(f"Error en ChatAnalyzerView: {str(e)}")
            return JsonResponse({
                'error': f'Error interno del servidor: {str(e)}'
            }, status=500)