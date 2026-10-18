from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config.settings import Settings


SYSTEM_PROMPT = """Eres JARVIS, un asistente de escritorio profesional, tranquilo y eficiente.
Hablas en español natural, con respuestas claras y concisas. Distingue los hechos de las
suposiciones y admite cuando no sabes algo. No afirmes haber ejecutado acciones: las tareas
del equipo solo se realizan mediante las herramientas permitidas de la aplicación. No pidas
ni guardes contraseñas, credenciales o datos financieros. El usuario controla la memoria."""


class ModelError(RuntimeError):
    pass


class ChatClient:
    """Small OpenAI-compatible client; works with local Ollama or compatible cloud APIs."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def reply(self, messages: list[dict[str, str]]) -> str:
        base = self.settings.base_url.strip().rstrip("/")
        if not base.startswith(("http://", "https://")):
            raise ModelError("La dirección del proveedor debe empezar por http:// o https://.")
        url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
        body = {
            "model": self.settings.model.strip(),
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            "temperature": 0.65,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        request = Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=55) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read(500).decode("utf-8", errors="replace")
            raise ModelError(f"El proveedor respondió HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ModelError(
                "No pude conectar con el modelo. Comprueba que Ollama esté iniciado, "
                "que el modelo esté descargado o que la URL y la conexión sean correctas."
            ) from exc
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise ModelError("El proveedor devolvió una respuesta que no pude interpretar.") from exc
        try:
            content = payload["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
            answer = str(content).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("La respuesta del modelo no contiene texto.") from exc
        if not answer:
            raise ModelError("El modelo devolvió una respuesta vacía.")
        return answer
