import sqlite3
from pathlib import Path
from sqlite3 import Connection
from typing import Callable, Generic, TypeVar

from pydantic import BaseModel

from eeva.interview import Interview

T = TypeVar("T", bound=BaseModel)  # Declare a type variable


class Table(Generic[T]):
    connection: Connection
    table_name: str
    from_json: Callable[[str], T]
    watchers: dict[int, dict[int, Callable[[T], None]]] = {}

    def __init__(self, table_name: str, db_path: Path, from_json: Callable[[str], T]) -> None:
        connection = sqlite3.connect(db_path.absolute())
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {table_name} TEXT NOT NULL
            )
            """
        )
        self.connection = connection
        self.table_name = table_name
        self.from_json = from_json

    def get(self, id: int) -> T:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT {self.table_name} FROM {self.table_name} WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"{self.table_name.capitalize()} with id {id} not found.")
        return self.from_json(row[0])

    def get_all(self) -> list[tuple[int, T]]:
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT id,{self.table_name} FROM {self.table_name}")
        rows = cursor.fetchall()
        return [(int(row[0]), self.from_json(row[1])) for row in rows]

    def create(self, item: T) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            f"INSERT INTO {self.table_name} ({self.table_name}) VALUES (?)",
            (item.model_dump_json(),),
        )
        self.connection.commit()
        if cursor.lastrowid is None:
            raise ValueError(f"Failed to create {self.table_name}.")
        return cursor.lastrowid

    def update(self, id: int, item: T) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            f"UPDATE {self.table_name} SET {self.table_name} = ? WHERE id = ?",
            (item.model_dump_json(), id),
        )
        self.connection.commit()
        for callback in self.watchers.get(id, {}).values():
            callback(item)

    def watch(self, id: int, key: int, callback: Callable[[T], None]) -> None:
        """
        Watch for changes to an item and call the callback with the updated item.
        """
        if id not in self.watchers:
            self.watchers[id] = {}
        self.watchers[id][key] = callback

    def unwatch(self, id: int, key: int) -> None:
        """
        Stop watching for changes to an item.
        """
        del self.watchers[id][key]

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

    def interviews(self) -> Table[Interview]:
        return Table[Interview](
            "interview",
            self.db_path,
            Interview.model_validate_json,
        )
