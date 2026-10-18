import sys

from PySide6.QtWidgets import QApplication

from config.settings import load_settings
from memory.store import MemoryStore
from ui.main_window import JarvisWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setOrganizationName("JARVIS")
    settings = load_settings()
    store = MemoryStore()
    window = JarvisWindow(settings, store)
    window.show()
    return app.exec()
