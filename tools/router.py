from __future__ import annotations

import re
import webbrowser
from datetime import datetime
from urllib.parse import quote

from memory.store import MemoryStore
from security.validation import normalize
from tools.apps import open_allowed_app
from tools.files import create_note, search_files
from tools.system import system_summary


class ToolRouter:
    def __init__(self, memory: MemoryStore):
        self.memory = memory

    def would_handle(self, text: str) -> bool:
        value = normalize(text)
        return bool(
            re.search(r"\b(abre|abrir|inicia|iniciar)\b", value)
            or re.search(r"\b(hora|fecha|recursos|cpu|memoria ram|estado del sistema)\b", value)
            or re.search(r"\b(recuerda|recorda|recordame|recu[eé]rdame)\b", value)
            or re.search(r"\b(crea|crear|escribe)\s+(una?\s+)?nota\b", value)
            or re.search(r"\b(busca|buscar|encuentra)\b", value)
            or re.search(r"\b(resume|resumir)\b", value)
            or re.search(r"\b(visita|visitar)\b", value)
            or ("volumen" in value and re.search(r"\b(baja|sube|ajusta|pon|cambia)\b", value))
            or re.search(r"\b(cierra|cerrar|apaga|apagar)\b", value)
            or re.search(r"\b(reproduce|reproducir|pausa|pausar|siguiente|anterior)\b", value)
            or re.search(r"\b(clima|tiempo meteorologico|pronostico)\b", value)
            or re.search(r"\b(rutina|automatizacion|automatiza)\b", value)
            or re.search(r"\b(recordatorio|recordatorios|notificacion|notificaciones)\b", value)
            or re.search(r"\b(organiza|organizar|ordena|ordenar|elimina|eliminar|borra|borrar|mueve|mover)\b", value)
            or re.search(r"\b(olvida|olvidar)\b", value)
        )

    def run(self, text: str) -> str | None:
        value = normalize(text).strip()
        if re.search(r"\b(que hora es|dime la hora|hora actual)\b", value):
            return f"Son las {datetime.now().astimezone().strftime('%H:%M')} de tu hora local."
        if re.search(r"\b(que fecha es|dime la fecha|fecha de hoy|que dia es hoy)\b", value):
            return f"Hoy es {datetime.now().astimezone().strftime('%d/%m/%Y')}."
        if re.search(r"\b(recursos|cpu|memoria ram|estado del sistema)\b", value):
            return system_summary()

        remember = re.search(r"\b(?:recuerda que|recorda que|recordame que|recuerdame que)\s+(.+)$", text, re.IGNORECASE)
        if remember:
            content = remember.group(1).strip().rstrip(".!?")
            if not content:
                return "¿Qué quieres que recuerde?"
            self.memory.add_memory(content, "tarea" if re.search(r"\b(tengo que|debo|pendiente|manana|hoy)\b", normalize(content)) else "dato")
            return "Lo guardé en tu memoria local. Puedes revisarlo, editarlo o eliminarlo desde el botón Memoria."
        if re.search(r"\b(que recuerdas|muestra mis recuerdos|mis recuerdos)\b", value):
            entries = self.memory.memories()
            if not entries:
                return "Tu memoria está vacía. Puedes pedirme que recuerde algo o agregarlo desde el panel Memoria."
            return "Esto es lo que tengo guardado:\n" + "\n".join(f"• {item['content']}" for item in entries[:12])

        note = re.search(r"\b(?:crea|crear|escribe)\s+(?:una?\s+)?nota(?:\s+(?:que diga|con|sobre))?\s*(.*)$", text, re.IGNORECASE)
        if note:
            content = note.group(1).strip().strip("\"'")
            if not content or normalize(content) in {"mis ideas", "mis pensamientos", "algo", "una idea"}:
                return "Dime el contenido de la nota, por ejemplo: «crea una nota con revisar el presupuesto»."
            if len(content) > 5000:
                return "La nota es demasiado larga; limita el contenido a 5000 caracteres."
            path = create_note(content, content[:42])
            return f"Creé la nota en {path}."

        search = re.search(r"\b(?:busca|buscar|encuentra)\s+(?:el\s+)?(?:archivo|documento|carpeta)\s+(?:llamado\s+)?(.+)$", text, re.IGNORECASE)
        if search:
            query = re.sub(r"\b(de mi proyecto|de mi|por favor)\b", "", normalize(search.group(1))).strip(" .?!") or "proyecto"
            matches = search_files(query)
            if not matches:
                return f"No encontré archivos cuyo nombre contenga «{query}» en Documentos, Escritorio o Descargas."
            return "Encontré estos archivos por nombre:\n" + "\n".join(f"• {path}" for path in matches)

        web_search = re.search(r"\b(?:busca|buscar)\s+(?:en internet\s+)?(?:informaci[oó]n\s+)?(?:sobre\s+)?(.+)$", text, re.IGNORECASE)
        if web_search and re.search(r"\b(internet|web|navegador|busca|buscar)\b", value):
            query = web_search.group(1).strip().strip(" .?!")
            if query and len(query) < 300:
                opened = webbrowser.open("https://www.google.com/search?q=" + quote(query))
                return f"Abrí una búsqueda web de «{query}»." if opened else "No pude abrir el navegador predeterminado."

        url_pattern = r"(https?://\S+|(?:www\.)?[\w-]+\.[a-z]{2,}(?:/\S*)?)"
        visit = re.search(r"\b(?:visita|visitar)\s+" + url_pattern, text, re.IGNORECASE)
        browser_request = re.search(r"\b(?:abre|abrir|inicia|iniciar)\s+(?:(?:mi|el)\s+)?navegador\b", text, re.IGNORECASE)
        browser_url = visit.group(1) if visit else None
        if browser_request or visit:
            if not browser_url and browser_request:
                after_browser = text[browser_request.end():]
                destination = re.search(url_pattern, after_browser, re.IGNORECASE)
                browser_url = destination.group(1) if destination else None
            url = (browser_url or "https://www.google.com").rstrip(".,!?;:")
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            opened = webbrowser.open(url)
            return f"Abrí {url}." if opened else "No pude abrir el navegador predeterminado."

        app = re.search(r"\b(?:abre|abrir|inicia|iniciar)\s+(?:el\s+|la\s+|mi\s+)?(.+)$", value)
        if app:
            candidate = app.group(1).strip(" .?!")
            if candidate in {"visual studio code", "vscode", "codigo", "bloc de notas", "notepad", "calculadora", "explorador", "explorador de archivos"}:
                return open_allowed_app(candidate)
            return "Esa aplicación no está en mi lista permitida. Puedo abrir VS Code, Bloc de notas, Calculadora o Explorador."

        if re.search(r"\b(baja|sube|ajusta|pon|cambia)\b", value) and "volumen" in value:
            return "El control de volumen del sistema aún no está habilitado en esta primera versión; no cambié ningún ajuste."
        if re.search(r"\b(cierra|cerrar|apaga|apagar)\b", value):
            return "Cerrar aplicaciones o apagar el equipo todavía no está habilitado. No realicé ningún cambio."
        if re.search(r"\b(clima|tiempo meteorologico|pronostico)\b", value):
            return "La consulta del clima requiere un proveedor de datos que todavía no está configurado. No inventé un pronóstico."
        if re.search(r"\b(rutina|automatizacion|automatiza)\b", value):
            return "Las rutinas automatizadas todavía no están configuradas. No inicié ninguna tarea."
        if re.search(r"\b(recordatorio|recordatorios|notificacion|notificaciones)\b", value):
            return "Puedo guardar una tarea si dices «recuerda que…», pero las alertas y recordatorios con hora todavía no están habilitados."
        if re.search(r"\b(organiza|organizar|ordena|ordenar|elimina|eliminar|borra|borrar|mueve|mover)\b", value):
            return "La organización, el movimiento y la eliminación de archivos todavía no están habilitados. No modifiqué ningún archivo."
        if re.search(r"\b(olvida|olvidar)\b", value):
            return "Puedes eliminar recuerdos desde el panel Memoria; no borré nada."
        if re.search(r"\b(reproduce|reproducir|pausa|pausar|siguiente|anterior)\b", value):
            return "El control multimedia todavía no está habilitado. No cambié la reproducción."
        if re.search(r"\b(resume|resumir)\b", value):
            return "Para resumirlo, usa Adjuntar texto y selecciona un archivo .txt o .md. El contenido seleccionado se enviará al modelo y no se guardará en el historial."
        return None
