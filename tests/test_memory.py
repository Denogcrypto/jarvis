import tempfile
import unittest
from pathlib import Path

from memory.store import MemoryStore


class MemoryStoreTests(unittest.TestCase):
    def test_messages_and_clear_history(self):
        with tempfile.TemporaryDirectory() as folder:
            store = MemoryStore(Path(folder) / "test.sqlite3")
            store.add_message("user", "Hola")
            store.add_message("assistant", "Buenas")
            self.assertEqual([m["content"] for m in store.recent_messages()], ["Hola", "Buenas"])
            store.clear_history()
            self.assertEqual(store.recent_messages(), [])

    def test_memory_can_be_added_edited_and_deleted(self):
        with tempfile.TemporaryDirectory() as folder:
            store = MemoryStore(Path(folder) / "test.sqlite3")
            identifier = store.add_memory("Prefiero respuestas breves", "preferencia")
            store.update_memory(identifier, "Prefiero respuestas concisas")
            self.assertEqual(store.memories()[0]["content"], "Prefiero respuestas concisas")
            store.delete_memory(identifier)
            self.assertEqual(store.memories(), [])


if __name__ == "__main__":
    unittest.main()
