import json
import re
import logging
from typing import Dict, List, Union, Any, Optional
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

class ChatAnalyzerService:
    """Servicio para analizar chats y extraer información específica usando OpenAI"""
    
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
        max_tokens: int = 250
    ) -> Dict[str, Any]:
        """
        Analizar historial de chat y extraer información específica
        
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
        1. DNI: Número peruano de 8 dígitos exactos
        2. Nombres: Solo nombres de pila
        3. Apellidos: Solo apellidos
        4. Celular: Número peruano que inicia con 9 y tiene 9 dígitos
        5. Monto: Solo si se menciona monto en soles o dólares (convertir dólares a soles usando tasa 3.65)
        6. Correo: Email válido
        7. Garantía: Si menciona garantía hipotecaria de un bien, responder: 'CASA', 'DEPARTAMENTO', 'LOCAL COMERCIAL' o 'TERRENOS INDUSTRIALES'
        8. Tiene_propiedad: true/false si tiene propiedad en registros públicos

        RESPONDE ÚNICAMENTE EN ESTE FORMATO JSON:
        {{
            "dni": "12345678",
            "nombres": "Juan Carlos",
            "apellidos": "Pérez García",
            "celular": "987654321",
            "monto": 15000,
            "correo": "juan@email.com",
            "garantia": "CASA",
            "tiene_propiedad": true
        }}

        Si no encuentras un dato, usa null. Para números usa valores numéricos, no strings.
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
            'dni': self._validate_dni(data.get('dni')),
            'nombres': self._validate_string(data.get('nombres')),
            'apellidos': self._validate_string(data.get('apellidos')),
            'celular': self._validate_celular(data.get('celular')),
            'monto': self._validate_monto(data.get('monto')),
            'correo': self._validate_email(data.get('correo')),
            'garantia': self._validate_garantia(data.get('garantia')),
            'tiene_propiedad': data.get('tiene_propiedad') if isinstance(data.get('tiene_propiedad'), bool) else None
        }
    
    def _validate_dni(self, dni: Any) -> Optional[str]:
        """Validar DNI peruano de 8 dígitos"""
        if not dni:
            return None
        dni_str = re.sub(r'\D', '', str(dni))
        return dni_str if len(dni_str) == 8 else None
    
    def _validate_string(self, string: Any) -> Optional[str]:
        """Validar string no vacío"""
        if not string or not isinstance(string, str):
            return None
        cleaned = string.strip()
        return cleaned if len(cleaned) > 0 else None
    
    def _validate_celular(self, celular: Any) -> Optional[str]:
        """Validar celular peruano (9 dígitos, inicia con 9)"""
        if not celular:
            return None
        celular_str = re.sub(r'\D', '', str(celular))
        return celular_str if len(celular_str) == 9 and celular_str.startswith('9') else None
    
    def _validate_monto(self, monto: Any) -> Optional[float]:
        """Validar monto numérico positivo"""
        if not monto:
            return None
        try:
            amount = float(monto)
            return amount if amount > 0 else None
        except (ValueError, TypeError):
            return None
    
    def _validate_email(self, email: Any) -> Optional[str]:
        """Validar formato de email"""
        if not email:
            return None
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return email if re.match(email_regex, str(email)) else None
    
    def _validate_garantia(self, garantia: Any) -> Optional[str]:
        """Validar tipo de garantía"""
        valid_garantias = ['CASA', 'DEPARTAMENTO', 'LOCAL COMERCIAL', 'TERRENOS INDUSTRIALES']
        return garantia if garantia in valid_garantias else None
    
    def _get_empty_result(self) -> Dict[str, None]:
        """Retornar estructura vacía"""
        return {
            'dni': None,
            'nombres': None,
            'apellidos': None,
            'celular': None,
            'monto': None,
            'correo': None,
            'garantia': None,
            'tiene_propiedad': None
        }


# Función de conveniencia para uso directo
def analyze_chat_conversation(
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