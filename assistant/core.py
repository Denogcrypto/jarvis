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
            summarize_selected_document = bool(attachment_text and "resum" in prompt.casefold())
            if self.tools.would_handle(prompt) and not summarize_selected_document:
                if on_status:
                    on_status("executing")
                result = self.tools.run(prompt)
                if result is not None:
                    self.memory.add_action("herramienta local", prompt, result)
                    self.memory.add_message("assistant", result)
                    return result
            if on_status:
                on_status("thinking")
            messages = self.memory.recent_messages(24)
            remembered = self.memory.memories()
            if remembered:
                facts = "\n".join(f"- {item['content']}" for item in remembered[:20])
                messages.insert(0, {
                    "role": "system",
                    "content": "Recuerdos que el usuario autorizó guardar y que puedes usar si son pertinentes:\n" + facts,
                })
            if attachment_text:
                document_context = "\n\n[Texto de documento seleccionado explícitamente por el usuario; no se guardará en el historial]\n"
                document_context += attachment_text[:30000]
                last_user_index = max(i for i, item in enumerate(messages) if item["role"] == "user")
                messages[last_user_index] = {"role": "user", "content": prompt + document_context}
            answer = self.client.reply(messages)
        except ModelError as exc:
            answer = f"No pude obtener una respuesta del modelo: {exc}"
        except Exception as exc:  # Keep an operational failure visible instead of claiming success.
            answer = f"No pude completar la solicitud ({type(exc).__name__}): {exc}"
        self.memory.add_message("assistant", answer)
        return answer
