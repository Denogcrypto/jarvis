# JARVIS · asistente personal de escritorio

Primera versión nativa para Windows, construida con Python y PySide6. La interfaz es una aplicación de escritorio, no una página web. Los módulos separan la UI, la conversación, el proveedor de IA, las herramientas permitidas, la voz, la configuración y la memoria.

## Arquitectura

- **PySide6** dibuja la interfaz y mantiene el trabajo de conversación, voz y síntesis fuera del hilo visual.
- **Python** coordina reglas locales y herramientas con listas permitidas; no hay ejecución de comandos arbitrarios.
- **Ollama local** es el proveedor sugerido para el modelo de lenguaje. `ai/client.py` usa el formato Chat Completions compatible con OpenAI, por lo que puede cambiarse por un proveedor compatible.
- **SQLite** guarda historial y recuerdos en `%APPDATA%\Jarvis\jarvis.sqlite3`.
- **SpeechRecognition** captura voz cuando el usuario habilita el micrófono. El modo inicial usa reconocimiento en línea en español; Vosk es opción local si se instala un modelo.
- **pyttsx3 / SAPI5** sintetiza voz local usando las voces instaladas en Windows.

## Estructura

```text
app/          ciclo de vida de la aplicación
assistant/    orquestación conversacional
ai/           cliente intercambiable de modelos
config/       configuración sin secretos
memory/       historial y recuerdos SQLite
security/     validación y política de datos sensibles
tools/        aplicaciones, notas, búsqueda y estado del equipo
voice/        reconocimiento y síntesis opcionales
ui/           ventana, animaciones, controles y workers Qt
tests/        pruebas de memoria, validación y enrutamiento
main.py       entrada de la aplicación
```

## Instalación y ejecución (Windows)

1. Instala Python 3.11 o posterior y, para la experiencia local, instala Ollama y descarga un modelo compatible, por ejemplo `ollama pull qwen2.5:7b`.
2. Ejecuta `run.bat`. El script crea `.venv`, instala `requirements.txt` y abre JARVIS. La primera instalación requiere conexión para descargar paquetes.
3. En la aplicación, abre **Ajustes** si quieres cambiar URL o nombre del modelo. Ollama debe estar ejecutándose en `http://localhost:11434`.
4. Para el acceso directo, ejecuta `crear_acceso_directo.ps1` después de la primera ejecución.

La instalación base de PySide6 puede obtenerse con `pip install PySide6`; el proyecto además instala `psutil` para los indicadores del equipo.

### Voz

Ejecuta `install_voice.bat` para instalar reconocimiento y TTS opcionales. Luego habilita el micrófono en JARVIS y pulsa **Pulsar para hablar**. La captura no es permanente: el indicador aparece durante la escucha y puedes apagar el micrófono. Google Speech Recognition envía el audio a su servicio para transcribirlo, requiere internet y su API pública puede cambiar o limitar solicitudes. Para voz sin conexión, instala `vosk`, descarga un modelo español compatible y define `JARVIS_STT=vosk` y `VOSK_MODEL_PATH` en el entorno. La voz de salida usa SAPI5 local; su naturalidad y el idioma dependen de las voces instaladas en Windows. **Detener voz** interrumpe la reproducción.

Windows puede requerir que habilites el acceso al micrófono para aplicaciones de escritorio en Configuración → Privacidad y seguridad → Micrófono.

### Proveedor de IA y claves

El perfil local predeterminado no requiere una clave. Para otro endpoint compatible, define las variables antes de abrir la app:

```powershell
[Environment]::SetEnvironmentVariable("JARVIS_BASE_URL", "https://api.ejemplo.com/v1", "User")
[Environment]::SetEnvironmentVariable("JARVIS_MODEL", "nombre-del-modelo", "User")
[Environment]::SetEnvironmentVariable("JARVIS_API_KEY", "tu-clave", "User")
.\.venv\Scripts\python.exe main.py
```

Reinicia JARVIS después de definirlas para que las lea desde el entorno de Windows. La aplicación lee la clave solo desde `JARVIS_API_KEY`, no la muestra ni la guarda en `settings.json`. El ejemplo `.env.example` documenta variables; no es un archivo de secretos ni se carga automáticamente.

## Capacidades que sí están implementadas

- Chat con contexto reciente; requiere un modelo accesible.
- Abrir VS Code (si `code` está en PATH), Bloc de notas, Calculadora y Explorador mediante una lista fija.
- Abrir búsquedas web en el navegador predeterminado.
- Buscar nombres de archivo bajo Documentos, Escritorio y Descargas, omitiendo directorios y nombres sensibles.
- Crear notas de texto en `%APPDATA%\Jarvis\Notas`.
- Consultar hora, fecha, CPU, memoria, almacenamiento y batería disponibles.
- Guardar, listar, editar y eliminar recuerdos a petición del usuario; borrar historial con confirmación.
- Ver el registro local de herramientas ejecutadas; borrar historial también borra ese registro.
- Adjuntar explícitamente archivos `.txt`/`.md` de hasta 1 MB para resumen; hasta 30 000 caracteres se envían al modelo y no se guardan en el historial.
- Indicadores visuales, conversación continua escrita y entrada de voz por pulsación.

## Límites de esta primera entrega

No hay activación continua por frase de palabra clave, control del volumen o reproducción multimedia, cierre de procesos, organización/movimiento de archivos, notificaciones de recordatorio, clima, lectura PDF, rutina automatizada, icono de bandeja ni instalador empaquetado. Estas órdenes reciben una respuesta explícita de no disponibilidad cuando son reconocidas. La voz de entrada y salida necesita sus paquetes/dispositivo/permisos; el modo Google necesita internet; Vosk necesita su modelo local. No se ejecutan comandos de shell generados por el modelo. Las herramientas con efectos sensibles se mantienen fuera de esta versión.

## Verificación

Con Python disponible, ejecuta:

```powershell
python -m unittest discover -v
```

Las pruebas usan SQLite temporal y no requieren modelo, micrófono ni acceso a archivos personales.

##
Con Openai

set "JARVIS_BASE_URL=https://api.openai.com/v1"
set "JARVIS_MODEL=gpt-5.4-mini"
set "JARVIS_API_KEY=PEGÁ_TU_CLAVE_ACÁ"
run.bat
