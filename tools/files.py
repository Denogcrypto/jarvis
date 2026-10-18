from __future__ import annotations

import os
from pathlib import Path


BLOCKED_DIR_PARTS = {"appdata", ".ssh", ".aws", ".azure", ".config", "credentials", "passwords"}
BLOCKED_NAME_PARTS = {"password", "credential", "secret", "token", "clave", "contraseña"}


def search_files(query: str, roots: list[Path] | None = None, max_results: int = 6) -> list[Path]:
    needle = query.strip().casefold()
    if not needle:
        return []
    if roots is None:
        home = Path.home()
        roots = [home / name for name in ("Documents", "Desktop", "Downloads")]
    results: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for current, dirs, files in os.walk(root, topdown=True):
            current_path = Path(current)
            dirs[:] = [d for d in dirs if not d.startswith(".") and d.casefold() not in BLOCKED_DIR_PARTS]
            if any(part.casefold() in BLOCKED_DIR_PARTS for part in current_path.parts):
                dirs[:] = []
                continue
            for filename in files:
                lowered = filename.casefold()
                if needle in lowered and not any(part in lowered for part in BLOCKED_NAME_PARTS):
                    results.append(current_path / filename)
                    if len(results) >= max_results:
                        return results
    return results


def create_note(content: str, title: str = "Nota") -> Path:
    from config.settings import data_directory
    from security.validation import safe_note_name

    notes_dir = data_directory() / "Notas"
    notes_dir.mkdir(parents=True, exist_ok=True)
    safe_title = safe_note_name(title)
    destination = notes_dir / f"{safe_title}.txt"
    suffix = 2
    while destination.exists():
        destination = notes_dir / f"{safe_title}-{suffix}.txt"
        suffix += 1
    destination.write_text(content.strip() + "\n", encoding="utf-8")
    return destination
