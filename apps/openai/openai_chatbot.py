import openai
from django.conf import settings
from .system_prompt.g_inversiones import (
    system_prompt_g_inversiones
)
from .system_prompt.presta_capital import (
    system_prompt_presta_capital,
    system_prompt_presta_capital_without_derivation
)

class ChatbotService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def get_response(self, brand, conversation_history = [], option = 1):
        # 1. Seleccionamos el system_prompt según la marca
        if brand == 4:
            prompt = system_prompt_g_inversiones()
        elif brand == 1:
            if option == 1:
                prompt = system_prompt_presta_capital()
            else:
                prompt = system_prompt_presta_capital_without_derivation()
        else:
            # En caso de que llegue una marca desconocida, puede usarse un prompt genérico
            prompt = (
                "Información Genérica:\n"
                "- Responde de forma amigable y profesional.\n"
                "- Si no reconoces la marca indicada, sugiere contactar a un asesor."
            )

        # 2. Construimos el array de mensajes
        messages = [{"role": "system", "content": prompt}]
        messages.extend(conversation_history) 
        
        # 3. Llamamos a la API
        try:
            resp = openai.chat.completions.create(
                model="gpt-4o", #gpt-3.5-turbo 
                messages=messages,
                max_tokens=250,
                temperature=0.3,  # Reduce creatividad, mejora consistencia
                top_p=0.7,       # Enfoque en respuestas más predecibles
                frequency_penalty=0.5,  # Evita repeticiones
                presence_penalty=0.3    # Fomenta concisión
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return "Disculpa, tengo problemas técnicos en este momento. Por favor, vuelve a contactar más tarde."
