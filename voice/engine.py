from __future__ import annotations

import json
import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal


class ListenWorker(QThread):
    status = Signal(str)
    transcript = Signal(str)
    error = Signal(str)

    def __init__(self, mode: str = "google", vosk_model_path: str = ""):
        super().__init__()
        self.mode = mode.casefold()
        self.vosk_model_path = vosk_model_path

    def run(self) -> None:
        try:
            import speech_recognition as sr
        except ImportError:
            self.error.emit("Falta la dependencia de voz. Instala requirements-voice.txt y vuelve a iniciar JARVIS.")
            return
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.status.emit("Calibrando micrófono…")
                recognizer.adjust_for_ambient_noise(source, duration=0.35)
                self.status.emit("Escuchando…")
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=14)
            if self.mode == "vosk":
                model_path = Path(self.vosk_model_path)
                if not model_path.is_dir():
                    self.error.emit("No encuentro el modelo Vosk. Configura VOSK_MODEL_PATH o cambia el modo a google.")
                    return
                recognized = recognizer.recognize_vosk(audio, language="es")
                text = json.loads(recognized).get("text", "").strip()
            else:
                text = recognizer.recognize_google(audio, language="es-AR").strip()
            if not text:
                self.error.emit("No se reconocieron palabras. Inténtalo otra vez.")
                return
            self.transcript.emit(text)
        except Exception as exc:
            name = type(exc).__name__
            if name in {"WaitTimeoutError", "UnknownValueError"}:
                message = "No pude entender el audio. Comprueba el micrófono y vuelve a intentarlo."
            elif name == "RequestError":
                message = "El reconocimiento de voz no está disponible. Revisa internet o configura Vosk local."
            elif name == "OSError":
                message = "No hay un micrófono disponible o Windows no concedió permiso. Revisa Configuración de privacidad."
            else:
                message = f"Falló la captura de voz ({name}): {exc}"
            self.error.emit(message)


class SpeechWorker(QThread):
    failed = Signal(str)

    def __init__(self, text: str, volume: float, rate: int):
        super().__init__()
        self.text = text
        self.volume = volume
        self.rate = rate
        self.engine = None

    def run(self) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            self.engine = engine
            engine.setProperty("volume", max(0.0, min(1.0, self.volume)))
            engine.setProperty("rate", self.rate)
            voices = engine.getProperty("voices") or []
            for voice in voices:
                signature = (voice.id + " " + voice.name + " " + str(voice.languages)).casefold()
                if "spanish" in signature or "es_" in signature or "es-" in signature or "español" in signature:
                    engine.setProperty("voice", voice.id)
                    break
            engine.say(self.text)
            engine.runAndWait()
        except Exception as exc:
            self.failed.emit(f"No pude generar voz ({type(exc).__name__}): {exc}")
        finally:
            self.engine = None

    def stop_speaking(self) -> None:
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass
