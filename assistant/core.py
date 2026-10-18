from __future__ import annotations

from typing import Callable

from ai.client import ChatClient, ModelError
from config.settings import Settings
from memory.store import MemoryStore
from security.validation import contains_sensitive_data
from tools.router import ToolRouter


class AssistantCore:
    def __init__(self, settings: Settings, memory: MemoryStore):
        self.settings = settings
        self.memory = memory
        self.client = ChatClient(settings)
        self.tools = ToolRouter(memory)

    def handle(self, text: str, attachment_text: str = "", on_status: Callable[[str], None] | None = None) -> str:
        prompt = text.strip()
        if not prompt:
            return "Escribe o dicta un mensaje para continuar."
        if contains_sensitive_data(prompt):
            safe = "[mensaje sensible omitido por privacidad]"
            self.memory.add_message("user", safe)
            answer = "Por privacidad, no proceso ni guardo contraseñas, credenciales, tokens o datos de tarjetas. Puedes reformular la solicitud sin incluir esos datos."
            self.memory.add_message("assistant", answer)
            return answer
        self.memory.add_message("user", prompt)
        try:
            if self.tools.would_handle(prompt):
                if on_status:
                    on_status("executing")
                result = self.tools.run(prompt)
                if result is not None:
                    self.memory.add_message("assistant", result)
                    return result
            if on_status:
                on_status("thinking")
            messages = self.memory.recent_messages(24)
            if attachment_text:
                document_context = "\n\n[Texto de documento seleccionado explícitamente por el usuario; no se guardará en el historial]\n"
                document_context += attachment_text[:30000]
                messages[-1] = {"role": "user", "content": prompt + document_context}
            answer = self.client.reply(messages)
        except ModelError as exc:
            answer = f"No pude obtener una respuesta del modelo: {exc}"
        except Exception as exc:  # Keep an operational failure visible instead of claiming success.
            answer = f"No pude completar la solicitud ({type(exc).__name__}): {exc}"
        self.memory.add_message("assistant", answer)
        return answer
