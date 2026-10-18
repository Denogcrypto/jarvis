import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from memory.store import MemoryStore
from security.validation import contains_sensitive_data, safe_note_name
from tools.router import ToolRouter


class ToolTests(unittest.TestCase):
    def test_remember_command_persists_only_explicit_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            store = MemoryStore(Path(folder) / "test.sqlite3")
            result = ToolRouter(store).run("JARVIS, recuerda que mañana termino el proyecto")
            self.assertIn("guardé", result.casefold())
            self.assertEqual(store.memories()[0]["content"], "mañana termino el proyecto")

    def test_sensitive_content_detection_and_note_name(self):
        self.assertTrue(contains_sensitive_data("mi contraseña es abc"))
        self.assertFalse(contains_sensitive_data("mañana termino mi proyecto"))
        self.assertEqual(safe_note_name("../Idea: uno?"), "Idea uno")

    def test_unknown_app_does_not_execute(self):
        with tempfile.TemporaryDirectory() as folder:
            router = ToolRouter(MemoryStore(Path(folder) / "test.sqlite3"))
            with patch("tools.router.webbrowser.open") as open_browser:
                result = router.run("abre una aplicación arbitraria")
            open_browser.assert_not_called()
            self.assertIn("lista permitida", result)

    def test_browser_search_opens_only_requested_query(self):
        with tempfile.TemporaryDirectory() as folder:
            router = ToolRouter(MemoryStore(Path(folder) / "test.sqlite3"))
            with patch("tools.router.webbrowser.open", return_value=True) as open_browser:
                result = router.run("abre mi navegador y busca información sobre inteligencia artificial")
            self.assertIn("Abrí una búsqueda web", result)
            self.assertIn("inteligencia%20artificial", open_browser.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
