from __future__ import annotations

import platform
from pathlib import Path


def system_summary() -> str:
    details = [f"Sistema: {platform.system()} {platform.release()}", f"Procesador: {platform.processor() or 'no disponible'}"]
    try:
        import psutil

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(Path.home().anchor or "/")
        details.append(f"CPU: {psutil.cpu_percent(interval=0.15):.0f}%")
        details.append(f"Memoria: {memory.percent:.0f}% usada ({memory.used // (1024**3)} / {memory.total // (1024**3)} GB)")
        details.append(f"Almacenamiento del sistema: {disk.percent:.0f}% usado")
        battery = psutil.sensors_battery()
        if battery:
            details.append(f"Batería: {battery.percent:.0f}%" + (" (conectada)" if battery.power_plugged else ""))
    except (ImportError, OSError, AttributeError):
        details.append("CPU, memoria y batería: instala las dependencias de requirements.txt para consultarlas.")
    return "\n".join(details)
