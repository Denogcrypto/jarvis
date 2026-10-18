import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from assistant.core import AssistantCore
from config.settings import Settings
from memory.store import MemoryStore


class AssistantCoreTests(unittest.TestCase):
    def make_core(self, folder):
        store = MemoryStore(Path(folder) / "test.sqlite3")
        return AssistantCore(Settings(), store), store

    def test_local_tool_action_is_recorded_without_model_call(self):
        with tempfile.TemporaryDirectory() as folder:
            core, store = self.make_core(folder)
            core.client.reply = Mock(side_effect=AssertionError("No debería llamar al modelo"))
            answer = core.handle("JARVIS, ¿qué hora es?")
            self.assertIn("hora local", answer)
            self.assertEqual(len(store.actions()), 1)
            self.assertEqual(store.actions()[0]["request"], "JARVIS, ¿qué hora es?")

    def test_selected_document_is_sent_but_not_persisted(self):
        with tempfile.TemporaryDirectory() as folder:
            core, store = self.make_core(folder)
            core.client.reply = Mock(return_value="El archivo describe una aplicación.")
            answer = core.handle("Resume este documento", "Texto privado de prueba")
            self.assertIn("aplicación", answer)
            sent_messages = core.client.reply.call_args.args[0]
            self.assertIn("Texto privado de prueba", sent_messages[-1]["content"])
            self.assertNotIn("Texto privado de prueba", str(store.conversation()))

    def test_sensitive_input_is_redacted_before_storage_or_model(self):
        with tempfile.TemporaryDirectory() as folder:
            core, store = self.make_core(folder)
            core.client.reply = Mock(side_effect=AssertionError("No debería enviar información sensible"))
            answer = core.handle("Recuerda que mi contraseña es confidencial")
            self.assertIn("Por privacidad", answer)
            self.assertEqual(store.conversation()[0]["content"], "[mensaje sensible omitido por privacidad]")
            self.assertEqual(store.memories(), [])


if __name__ == "__main__":
    unittest.main()
