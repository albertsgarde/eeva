import sqlite3
from pathlib import Path
from sqlite3 import Connection
from typing import Any, Callable, Generic, Type, TypeVar

from eeva.form import Form
from eeva.form_response import FormResponse
from eeva.interview import Interview
from eeva.prompt import Prompt
from eeva.question import Question
from eeva.utils import NetworkModel

type KeyType = int | str  # Define a type for keys that can be either int or str

T = TypeVar("T", bound=NetworkModel)  # Declare a type variable
K = TypeVar("K", bound=int | str)  # Declare a type variable for keys


def sqlite_key(key_type: Type[K]) -> str:
    if key_type is int:
        return "INTEGER"
    elif key_type is str:
        return "TEXT"
    else:
        raise TypeError("Unsupported type")


def from_sqlite_value(key_type: Type[K], value: Any) -> K:
    if key_type is int:
        return int(value)  # type: ignore
    elif key_type is str:
        return str(value)  # type: ignore
    else:
        raise TypeError("Unsupported type for SQLite value conversion")


class Table(Generic[K, T]):
    connection: Connection
    table_name: str
    from_json: Callable[[str], T]
    watchers: dict[K, dict[int, Callable[[T], None]]] = {}
    key_type: Type[K]

    def __init__(self, table_name: str, db_path: Path, from_json: Callable[[str], T], key_type: Type[K]) -> None:
        connection = sqlite3.connect(db_path.absolute())
        if key_type is int:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {table_name} TEXT NOT NULL
                )
                """
            )
        elif key_type is str:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY NOT NULL,
                    {table_name} TEXT NOT NULL
                )
                """
            )
        else:
            raise TypeError("Unsupported key type.")
        self.connection = connection
        self.table_name = table_name
        self.from_json = from_json
        self.key_type = key_type

    def exists(self, id: K) -> bool:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT 1 FROM {self.table_name} WHERE id = ?", (id,))
        return cursor.fetchone() is not None

    def get(self, id: K) -> T:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT {self.table_name} FROM {self.table_name} WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"{self.table_name.capitalize()} with id {id} not found.")
        return self.from_json(row[0])

    def get_all(self) -> list[tuple[K, T]]:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT id,{self.table_name} FROM {self.table_name}")
        rows = cursor.fetchall()

        return [(from_sqlite_value(self.key_type, row[0]), self.from_json(row[1])) for row in rows]

    def create(self, item: T) -> int:
        if self.key_type is str:
            raise ValueError("Key must be provided for string keys. Use create_with_key instead.")
        cursor = self.connection.cursor()
        cursor.execute(
            f"INSERT INTO {self.table_name} ({self.table_name}) VALUES (?)",
            (item.model_dump_json(),),
        )
        if cursor.lastrowid is None:
            raise ValueError(f"Failed to create {self.table_name}.")
        self.connection.commit()
        return cursor.lastrowid

    def create_with_id(self, item: T, id: K):
        cursor = self.connection.cursor()
        cursor.execute(
            f"INSERT INTO {self.table_name} (id, {self.table_name}) VALUES (?, ?)",
            (id, item.model_dump_json()),
        )
        self.connection.commit()

    def update(self, id: K, item: T) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            f"UPDATE {self.table_name} SET {self.table_name} = ? WHERE id = ?",
            (item.model_dump_json(), id),
        )
        self.connection.commit()
        for callback in self.watchers.get(id, {}).values():
            callback(item)

    def upsert(self, id: K, item: T) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
INSERT INTO {self.table_name} (id, {self.table_name})
VALUES (:id, :value)
ON CONFLICT(id) DO UPDATE SET
    {self.table_name} = :value
""",
            {"id": id, "value": item.model_dump_json()},
        )
        self.connection.commit()
        for callback in self.watchers.get(id, {}).values():
            callback(item)

    def watch(self, id: K, key: int, callback: Callable[[T], None]) -> None:
        """
        Watch for changes to an item and call the callback with the updated item.
        """
        if id not in self.watchers:
            self.watchers[id] = {}
        self.watchers[id][key] = callback

    def unwatch(self, id: K, key: int) -> None:
        """
        Stop watching for changes to an item.
        """
        del self.watchers[id][key]

    def delete(self, id: K) -> None:
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (id,))
        self.connection.commit()
        if id in self.watchers:
            del self.watchers[id]

    def clear(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM {self.table_name}")
        self.connection.commit()


class Database:
    db_path: Path

    def __init__(self, db_path: Path) -> None:
        """Connect to the SQLite database."""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

    def interviews(self) -> Table[int, Interview]:
        return Table[int, Interview](
            "interview",
            self.db_path,
            Interview.model_validate_json,
            key_type=int,
        )

    def prompts(self) -> Table[str, Prompt]:
        return Table[str, Prompt](
            "prompt",
            self.db_path,
            Prompt.model_validate_json,
            key_type=str,
        )

    def questions(self) -> Table[str, Question]:
        return Table[str, Question](
            "question",
            self.db_path,
            Question.model_validate_json,
            key_type=str,
        )

    def forms(self) -> Table[str, Form]:
        return Table[str, Form](
            "form",
            self.db_path,
            Form.model_validate_json,
            key_type=str,
        )

    def form_responses(self) -> Table[int, FormResponse]:
        return Table[int, FormResponse](
            "form_response",
            self.db_path,
            FormResponse.model_validate_json,
            key_type=int,
        )
