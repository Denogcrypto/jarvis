from __future__ import annotations

import os
import shutil
import subprocess
import sys


APP_ALIASES = {
    "visual studio code": "vscode",
    "visual studio code": "vscode",
    "vscode": "vscode",
    "código": "vscode",
    "codigo": "vscode",
    "bloc de notas": "notepad",
    "notepad": "notepad",
    "calculadora": "calculator",
    "explorador de archivos": "explorer",
    "explorador": "explorer",
}


def open_allowed_app(name: str) -> str:
    key = APP_ALIASES.get(name.casefold().strip())
    if not key:
        return "Solo puedo abrir aplicaciones incluidas en mi lista permitida: Visual Studio Code, Bloc de notas, Calculadora y Explorador."
    if sys.platform == "win32":
        targets = {"vscode": "code", "notepad": "notepad.exe", "calculator": "calc.exe", "explorer": "explorer.exe"}
        target = targets[key]
        if key == "vscode":
            executable = shutil.which(target)
            if not executable:
                return "No encontré el comando 'code'. Instala VS Code o habilita 'code' en PATH."
            subprocess.Popen([executable], close_fds=True)
        else:
            os.startfile(target)  # type: ignore[attr-defined]  # Windows ShellExecute, fixed allow-list only.
    elif sys.platform == "darwin":
        target = {"vscode": "Visual Studio Code", "notepad": "TextEdit", "calculator": "Calculator", "explorer": "Finder"}[key]
        subprocess.Popen(["open", "-a", target], close_fds=True)
    else:
        targets = {"vscode": "code", "notepad": "gedit", "calculator": "gnome-calculator", "explorer": "xdg-open"}
        executable = shutil.which(targets[key])
        if not executable:
            return f"No encontré {targets[key]} en este equipo."
        args = [executable, "."] if key == "explorer" else [executable]
        subprocess.Popen(args, close_fds=True)
    return f"Abrí {name} correctamente."
