import json
import re
import logging
from typing import Dict, List, Union, Any, Optional
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger(__name__)

class ChatAnalyzerService:
    """Servicio mejorado para analizar chats y extraer 4 criterios específicos"""
    
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
        model: str = "gpt-4o",
        temperature: float = 0.1,
        max_tokens: int = 300
    ) -> Dict[str, Any]:
        """
        Analizar historial de chat y extraer los 4 criterios específicos
        
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
            # 1. Crear el prompt de análisis mejorado
            prompt = self._create_improved_analysis_prompt(chat_history)
            
            # 2. Llamada a OpenAI
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un experto analizador de conversaciones financieras especializando en préstamos hipotecarios. 
                        Analiza con precisión cada criterio y responde únicamente en el formato JSON solicitado.
                        Sé estricto en la interpretación: solo responde true si la información está explícitamente mencionada."""
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
    
    def _create_improved_analysis_prompt(self, chat_history: Union[List[Dict], str]) -> str:
        """Crear el prompt de análisis mejorado con los 4 criterios específicos"""
        if isinstance(chat_history, list):
            chat_text = '\n'.join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                for msg in chat_history
            ])
        else:
            chat_text = str(chat_history)
        
        return f"""
        Analiza el siguiente historial de chat y evalúa ÚNICAMENTE los 4 criterios específicos solicitados.
        Sé preciso y estricto: solo responde true si la información está EXPLÍCITAMENTE mencionada.

        HISTORIAL DE CHAT:
        {chat_text}

        CRITERIOS A EVALUAR:

        1. TIENE_PROPIEDAD: 
           - true: Si el cliente menciona que TIENE o POSEE una propiedad (casa, departamento, terreno, local comercial, etc.)
           - false: Si explícitamente dice que NO tiene propiedad
           - null: Si no se menciona nada sobre tener propiedades

        2. PROPIEDAD_EN_REGISTROS_PUBLICOS:
           - true: Si menciona que su propiedad ESTÁ INSCRITA en Registros Públicos, SUNARP, o tiene títulos registrados
           - false: Si dice que NO está inscrita o no tiene papeles en regla
           - null: Si no se menciona nada sobre inscripción registral

        3. PRESTAMO_MAYOR_20000:
           - true: Si menciona necesitar un préstamo MAYOR a S/20,000 soles (o equivalente en dólares > $5,333)
           - false: Si menciona un monto MENOR a S/20,000
           - null: Si no menciona monto específico de préstamo

        4. UBICACION_INMUEBLE:
           - Texto: Si menciona ubicación específica (distrito, provincia, dirección, zona, etc.)
           - null: Si no menciona ubicación del inmueble

        EJEMPLOS DE INTERPRETACIÓN:
        - "Tengo una casa" → tiene_propiedad: true
        - "Mi casa está inscrita en registros públicos" → propiedad_en_registros_publicos: true
        - "Necesito 50,000 soles" → prestamo_mayor_20000: true
        - "Mi casa está en San Isidro" → ubicacion_inmueble: "San Isidro"
        - "No tengo propiedades" → tiene_propiedad: false
        - "Quiero 15,000 soles" → prestamo_mayor_20000: false

        CONVERSIÓN DE DIVISAS:
        - Si menciona dólares, convertir a soles usando tasa 3.75
        - $6,000 = S/22,500 → prestamo_mayor_20000: true
        - $5,000 = S/18,750 → prestamo_mayor_20000: false

        RESPONDE ÚNICAMENTE EN ESTE FORMATO JSON EXACTO:
        {{
            "tiene_propiedad": true,
            "propiedad_en_registros_publicos": false,
            "prestamo_mayor_20000": true,
            "ubicacion_inmueble": "San Isidro, Lima"
        }}

        REGLAS ESTRICTAS:
        - Solo usa true/false cuando la información esté EXPLÍCITAMENTE mencionada
        - Usa null cuando no haya información clara
        - Para ubicacion_inmueble usa el texto exacto mencionado o null
        - No hagas suposiciones, solo analiza lo que está claramente expresado
        - Responde SOLO el JSON, sin explicaciones adicionales
        """
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parsear la respuesta de OpenAI y extraer el JSON"""
        try:
            # Limpiar respuesta y buscar JSON
            cleaned_response = response.strip()
            
            # Buscar el JSON en la respuesta
            json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
            if not json_match:
                raise ValueError('No se encontró JSON válido en la respuesta')
            
            json_str = json_match.group(0)
            parsed_data = json.loads(json_str)
            
            # Validar que contiene las claves esperadas
            expected_keys = ['tiene_propiedad', 'propiedad_en_registros_publicos', 'prestamo_mayor_20000', 'ubicacion_inmueble']
            for key in expected_keys:
                if key not in parsed_data:
                    parsed_data[key] = None
                    
            return parsed_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f'Error al parsear respuesta: {e}. Respuesta: {response}')
            return self._get_empty_result()
    
    def _validate_and_clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar y limpiar los datos extraídos según los 4 criterios"""
        return {
            'tiene_propiedad': self._validate_boolean_or_null(data.get('tiene_propiedad')),
            'propiedad_en_registros_publicos': self._validate_boolean_or_null(data.get('propiedad_en_registros_publicos')),
            'prestamo_mayor_20000': self._validate_boolean_or_null(data.get('prestamo_mayor_20000')),
            'ubicacion_inmueble': self._validate_ubicacion(data.get('ubicacion_inmueble'))
        }
    
    def _validate_boolean_or_null(self, value: Any) -> Optional[bool]:
        """Validar valores booleanos o null"""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['true', 'verdadero', 'si', 'sí']:
                return True
            elif value_lower in ['false', 'falso', 'no']:
                return False
        return None
    
    def _validate_ubicacion(self, ubicacion: Any) -> Optional[str]:
        """Validar y limpiar ubicación del inmueble"""
        if not ubicacion:
            return None
        if isinstance(ubicacion, str):
            cleaned = ubicacion.strip()
            return cleaned if len(cleaned) > 0 else None
        return None
    
    def _get_empty_result(self) -> Dict[str, None]:
        """Retornar estructura vacía con los 4 criterios"""
        return {
            'tiene_propiedad': None,
            'propiedad_en_registros_publicos': None,
            'prestamo_mayor_20000': None,
            'ubicacion_inmueble': None
        }
    
    def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Generar resumen legible del análisis
        
        Args:
            analysis_result: Resultado del análisis
            
        Returns:
            Dict con resumen en texto legible
        """
        if not analysis_result.get('success', False):
            return {'summary': 'Error en el análisis'}
        
        data = analysis_result.get('data', {})
        
        summary_parts = []
        
        # Tiene propiedad
        if data.get('tiene_propiedad') is True:
            summary_parts.append("✅ Cliente tiene propiedad")
        elif data.get('tiene_propiedad') is False:
            summary_parts.append("❌ Cliente no tiene propiedad")
        else:
            summary_parts.append("❓ No se menciona si tiene propiedad")
        
        # Registros públicos
        if data.get('propiedad_en_registros_publicos') is True:
            summary_parts.append("✅ Propiedad inscrita en Registros Públicos")
        elif data.get('propiedad_en_registros_publicos') is False:
            summary_parts.append("❌ Propiedad NO inscrita en Registros Públicos")
        else:
            summary_parts.append("❓ No se menciona inscripción registral")
        
        # Préstamo mayor a 20,000
        if data.get('prestamo_mayor_20000') is True:
            summary_parts.append("✅ Solicita préstamo mayor a S/20,000")
        elif data.get('prestamo_mayor_20000') is False:
            summary_parts.append("❌ Solicita préstamo menor a S/20,000")
        else:
            summary_parts.append("❓ No se menciona monto específico")
        
        # Ubicación
        if data.get('ubicacion_inmueble'):
            summary_parts.append(f"📍 Ubicación: {data.get('ubicacion_inmueble')}")
        else:
            summary_parts.append("❓ No se menciona ubicación del inmueble")
        
        return {
            'summary': ' | '.join(summary_parts),
            'detailed': summary_parts
        }

# Función de conveniencia mejorada
def analyze_chat_improved(
    chat_history: Union[List[Dict[str, str]], str],
    api_key: str = None,
    include_summary: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Función de conveniencia para analizar un chat con los 4 criterios mejorados
    
    Args:
        chat_history: Lista de mensajes o string con el historial
        api_key: Clave API de OpenAI (opcional)
        include_summary: Si incluir resumen legible
        **kwargs: Argumentos adicionales para el análisis
        
    Returns:
        Dict con los datos extraídos, validados y opcionalmente con resumen
    """
    analyzer = ChatAnalyzerService(api_key=api_key)
    result = analyzer.analyze_chat(chat_history, **kwargs)
    
    if include_summary and result.get('success', False):
        result['summary'] = analyzer.get_analysis_summary(result)
    
    return result

# Decorador mejorado para manejar errores
def handle_chat_analysis_errors(func):
    """Decorador mejorado para manejar errores comunes en análisis de chat"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.warning(f'Error de validación en análisis: {str(e)}')
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

# Ejemplo de uso en vista Django
"""
# En tu vista Django:
from .services import analyze_chat_improved

def analyze_chat_view(request):
    chat_history = request.POST.get('chat_history')
    
    result = analyze_chat_improved(
        chat_history=chat_history,
        include_summary=True
    )
    
    if result['success']:
        data = result['data']
        summary = result.get('summary', {})
        
        # Usar los datos para lógica de negocio
        if data['tiene_propiedad'] and data['propiedad_en_registros_publicos'] and data['prestamo_mayor_20000']:
            # Cliente califica para préstamo hipotecario
            pass
            
    return JsonResponse(result)
"""