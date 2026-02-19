"""Database connection factory supporting SQL Server and SQLite."""

import re
import sqlite3
from dataclasses import dataclass
from typing import Protocol


class DatabaseConnection(Protocol):
    """Protocol for database connections."""

    def cursor(self): ...
    def commit(self): ...
    def close(self): ...


class SQLiteConnection:
    """SQLite connection wrapper that converts @param to ? placeholders."""

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def cursor(self) -> "SQLiteCursor":
        return SQLiteCursor(self._conn.cursor())

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


class SQLiteCursor:
    """SQLite cursor wrapper that converts @param to ? placeholders."""

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor
        self._param_names: list[str] = []

    def execute(self, sql: str, params: dict | None = None) -> "SQLiteCursor":
        """Execute SQL, converting @param syntax to ? placeholders."""
        converted_sql, param_values = self._convert_params(sql, params or {})
        self._cursor.execute(converted_sql, param_values)
        return self

    def _convert_params(self, sql: str, params: dict) -> tuple[str, list]:
        """Convert @param syntax to ? and return ordered param values."""
        self._param_names = []
        pattern = r"@(\w+)"

        def replace_param(match):
            param_name = match.group(1)
            self._param_names.append(param_name)
            return "?"

        converted_sql = re.sub(pattern, replace_param, sql)
        param_values = [params.get(name) for name in self._param_names]
        return converted_sql, param_values

    def fetchall(self) -> list:
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()

    def close(self) -> None:
        self._cursor.close()

    @property
    def description(self):
        return self._cursor.description


@dataclass
class DatabaseConfig:
    """Database connection configuration."""

    driver: str = "sqlserver"  # 'sqlserver' or 'sqlite'
    host: str = ""
    port: int = 1433
    database: str = ""
    username: str = ""
    password: str = ""
    sqlite_path: str = ""  # For SQLite testing


def get_connection(config: DatabaseConfig) -> DatabaseConnection:
    """Get a database connection based on configuration."""
    if config.driver == "sqlite":
        return SQLiteConnection(config.sqlite_path)
    elif config.driver == "sqlserver":
        import pyodbc

        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config.host},{config.port};"
            f"DATABASE={config.database};"
            f"UID={config.username};"
            f"PWD={config.password}"
        )
        return pyodbc.connect(connection_string)
    else:
        raise ValueError(f"Unsupported driver: {config.driver}")


def check_connection(config: DatabaseConfig) -> tuple[bool, str]:
    """Check database connection, returns (success, message)."""
    try:
        conn = get_connection(config)
        cursor = conn.cursor()
        if config.driver == "sqlite":
            cursor.execute("SELECT 1")
        else:
            cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)
