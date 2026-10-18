from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


def data_directory() -> Path:
    root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    path = root / "Jarvis"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class Settings:
    base_url: str = "http://localhost:11434/v1"
    model: str = "qwen2.5:7b"
    voice_volume: float = 0.85
    voice_rate: int = 178
    auto_speak: bool = False
    stt_mode: str = "google"

    @property
    def api_key(self) -> str:
        # Deliberately read only from the environment; never serialized or shown in the UI.
        return os.environ.get("JARVIS_API_KEY", "")

    @property
    def vosk_model_path(self) -> str:
        return os.environ.get("VOSK_MODEL_PATH", "")


def load_settings() -> Settings:
    path = data_directory() / "settings.json"
    saved: dict = {}
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    settings = Settings(
        base_url=os.environ.get("JARVIS_BASE_URL", saved.get("base_url", "http://localhost:11434/v1")),
        model=os.environ.get("JARVIS_MODEL", saved.get("model", "qwen2.5:7b")),
        voice_volume=float(saved.get("voice_volume", 0.85)),
        voice_rate=int(saved.get("voice_rate", 178)),
        auto_speak=bool(saved.get("auto_speak", False)),
        stt_mode=os.environ.get("JARVIS_STT", saved.get("stt_mode", "google")),
    )
    settings.voice_volume = min(1.0, max(0.0, settings.voice_volume))
    settings.voice_rate = min(280, max(100, settings.voice_rate))
    return settings


def save_settings(settings: Settings) -> None:
    path = data_directory() / "settings.json"
    # API keys and other secrets are intentionally excluded.
    saved = asdict(settings)
    saved.pop("api_key", None)
    saved.pop("vosk_model_path", None)
    path.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
