import os
import sqlite3
from pathlib import Path
from typing import Iterable


def _connect(database_path: str) -> sqlite3.Connection:
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: str) -> None:
    with _connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'model')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_history "
            "ON messages(chat_id, user_id, id DESC)"
        )


def get_history(database_path: str, chat_id: int, user_id: int, limit: int) -> list[dict[str, str]]:
    if limit <= 0:
        return []
    with _connect(database_path) as connection:
        rows = connection.execute(
            "SELECT role, content FROM messages "
            "WHERE chat_id = ? AND user_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, user_id, limit),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def save_exchange(
    database_path: str, chat_id: int, user_id: int, user_text: str, answer: str
) -> None:
    with _connect(database_path) as connection:
        connection.executemany(
            "INSERT INTO messages(chat_id, user_id, role, content) VALUES (?, ?, ?, ?)",
            [
                (chat_id, user_id, "user", user_text),
                (chat_id, user_id, "model", answer),
            ],
        )


def clear_history(database_path: str, chat_id: int, user_id: int) -> None:
    with _connect(database_path) as connection:
        connection.execute(
            "DELETE FROM messages WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        )
