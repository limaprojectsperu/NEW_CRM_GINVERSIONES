# services/chatbot.py
import openai
from django.conf import settings
from .system_prompt.g_inversiones import system_prompt_g_inversiones

class ChatbotService:
    def __init__(self):
        # Esto sí se ejecutará al instanciar ChatbotService
        openai.api_key = settings.OPENAI_API_KEY
        self.system_prompt = system_prompt_g_inversiones()

    def get_response(self, user_message, conversation_history=None):
        # Construyo el prompt completo
        messages = [{"role": "system", "content": self.system_prompt}]
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = "user" if msg.is_user_message else "assistant"
                messages.append({"role": role, "content": msg.message_text})
        messages.append({"role": "user", "content": user_message})

        try:
            resp = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=60,
                temperature=0.7
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            # Devuelvo solo el texto de la excepción, así no intento serializar objetos internos
            return str(e)
            
