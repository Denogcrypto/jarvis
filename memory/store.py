from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from config.settings import data_directory


class MemoryStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else data_directory() / "jarvis.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL DEFAULT 'dato',
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def add_message(self, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Rol de conversación inválido")
        with self._connect() as db:
            db.execute("INSERT INTO messages(role,content,created_at) VALUES(?,?,?)", (role, content, self._now()))

    def recent_messages(self, limit: int = 24) -> list[dict[str, str]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT role,content FROM messages ORDER BY id DESC LIMIT ?", (max(1, min(limit, 100)),)
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def conversation(self, limit: int = 200) -> list[dict[str, str]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT role,content,created_at FROM messages ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def clear_history(self) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM messages")

    def add_memory(self, content: str, category: str = "dato") -> int:
        value = content.strip()
        if not value or len(value) > 1000:
            raise ValueError("El recuerdo debe tener entre 1 y 1000 caracteres")
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO memories(category,content,created_at) VALUES(?,?,?)",
                (category[:40], value, self._now()),
            )
            return int(cursor.lastrowid)

    def memories(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT id,category,content,created_at FROM memories ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

    def update_memory(self, memory_id: int, content: str) -> None:
        value = content.strip()
        if not value or len(value) > 1000:
            raise ValueError("El recuerdo debe tener entre 1 y 1000 caracteres")
        with self._connect() as db:
            db.execute("UPDATE memories SET content=? WHERE id=?", (value, memory_id))

    def delete_memory(self, memory_id: int) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM memories WHERE id=?", (memory_id,))

    def clear_memories(self) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM memories")
