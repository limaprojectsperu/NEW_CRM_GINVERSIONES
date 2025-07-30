import json
import re
import logging
from typing import Dict, List, Union, Any, Optional
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

class ChatAnalyzerService:
    """Servicio simplificado para analizar chats y extraer monto, tipo de propiedad y si tiene propiedad"""
    
    def __init__(self, api_key: str = None):
        """
        Inicializar el servicio
        
        Args:
            api_key: Clave API de OpenAI. Si no se proporciona, usa settings.OPENAI_API_KEY
        """
        self.openai_client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY)
    
    def analyze_chat(
        self, 
        chat_history: Union[List[Dict[str, str]], str],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.1,
        max_tokens: int = 200
    ) -> Dict[str, Any]:
        """
        Analizar historial de chat y extraer información específica: monto, tipo de propiedad y si tiene propiedad
        
        Args:
            chat_history: Lista de mensajes o string con el historial
            model: Modelo de OpenAI a usar
            temperature: Temperatura para la generación
            max_tokens: Máximo número de tokens
            
        Returns:
            Dict con los datos extraídos y validados
            
        Raises:
            ValueError: Si el chat_history está vacío
            Exception: Para errores de OpenAI o procesamiento
        """
        if not chat_history:
            raise ValueError("El historial de chat es requerido")
        
        try:
            # 1. Crear el prompt de análisis
            prompt = self._create_analysis_prompt(chat_history)
            
            # 2. Llamada a OpenAI
            response = self.openai_client.chat.completions.create(
                model=model,
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
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            raw_result = response.choices[0].message.content
            
            # 3. Parsear y validar la respuesta
            parsed_data = self._parse_response(raw_result)
            validated_data = self._validate_and_clean_data(parsed_data)
            
            return {
                'success': True,
                'data': validated_data,
                'raw_response': raw_result,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de chat: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': self._get_empty_result(),
                'usage': None
            }
    
    def _create_analysis_prompt(self, chat_history: Union[List[Dict], str]) -> str:
        """Crear el prompt de análisis a partir del historial de chat"""
        if isinstance(chat_history, list):
            chat_text = '\n'.join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                for msg in chat_history
            ])
        else:
            chat_text = str(chat_history)
        
        return f"""
        Analiza el siguiente historial de chat y extrae ÚNICAMENTE la información solicitada. 
        Si no encuentras algún dato, responde con null.

        HISTORIAL DE CHAT:
        {chat_text}

        INFORMACIÓN A EXTRAER:
        1. Monto: Solo si se menciona monto en soles o dólares (convertir dólares a soles usando tasa 3.75)
        2. Tipo_propiedad: Si menciona una propiedad como garantía, responder: 'CASA', 'DEPARTAMENTO', 'LOCAL COMERCIAL' o 'TERRENOS INDUSTRIALES'
        3. Tiene_propiedad: true/false si explícitamente menciona que tiene propiedad en registros públicos

        RESPONDE ÚNICAMENTE EN ESTE FORMATO JSON:
        {{
            "monto": 15000,
            "tipo_propiedad": "CASA",
            "tiene_propiedad": true
        }}

        Si no encuentras un dato, usa null. Para el monto usa valores numéricos, no strings.
        Para tiene_propiedad usa true/false solo si está claramente mencionado, sino null.
        """
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parsear la respuesta de OpenAI y extraer el JSON"""
        try:
            # Buscar el JSON en la respuesta
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                raise ValueError('No se encontró JSON válido en la respuesta')
            
            parsed_data = json.loads(json_match.group(0))
            return parsed_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f'Error al parsear respuesta: {e}')
            return {}
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar y limpiar los datos extraídos"""
        return {
            'monto': self._validate_monto(data.get('monto')),
            'tipo_propiedad': data.get('tipo_propiedad'),
            'tiene_propiedad': self._validate_tiene_propiedad(data.get('tiene_propiedad'))
        }
    
    def _validate_monto(self, monto: Any) -> Optional[float]:
        """Validar monto numérico positivo"""
        if not monto:
            return None
        try:
            amount = float(monto)
            return amount if amount > 0 else None
        except (ValueError, TypeError):
            return None
    
    def _validate_tipo_propiedad(self, tipo_propiedad: Any) -> Optional[str]:
        """Validar tipo de propiedad"""
        valid_tipos = ['CASA', 'DEPARTAMENTO', 'LOCAL COMERCIAL', 'TERRENOS INDUSTRIALES']
        return tipo_propiedad if tipo_propiedad in valid_tipos else None
    
    def _validate_tiene_propiedad(self, tiene_propiedad: Any) -> Optional[bool]:
        """Validar si tiene propiedad (solo true/false explícitos)"""
        if isinstance(tiene_propiedad, bool):
            return tiene_propiedad
        return None
    
    def _get_empty_result(self) -> Dict[str, None]:
        """Retornar estructura vacía"""
        return {
            'monto': None,
            'tipo_propiedad': None,
            'tiene_propiedad': None
        }

# Función de conveniencia para uso directo
def analyze_chat_simple(
    chat_history: Union[List[Dict[str, str]], str],
    api_key: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Función de conveniencia para analizar un chat sin instanciar la clase
    
    Args:
        chat_history: Lista de mensajes o string con el historial
        api_key: Clave API de OpenAI (opcional)
        **kwargs: Argumentos adicionales para el análisis
        
    Returns:
        Dict con los datos extraídos y validados
    """
    analyzer = ChatAnalyzerService(api_key=api_key)
    return analyzer.analyze_chat(chat_history, **kwargs)

# Decorador para manejar errores comunes en vistas
def handle_chat_analysis_errors(func):
    """Decorador para manejar errores comunes en análisis de chat"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return {
                'success': False,
                'error': f'Error de validación: {str(e)}',
                'data': ChatAnalyzerService()._get_empty_result()
            }
        except Exception as e:
            logger.error(f'Error inesperado en análisis de chat: {str(e)}')
            return {
                'success': False,
                'error': 'Error interno del servidor',
                'data': ChatAnalyzerService()._get_empty_result()
            }
    return wrapper