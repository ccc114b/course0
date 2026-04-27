"""
sqlite_cjk_fts: CJK Bigram Tokenizer for SQLite FTS5.

Usage:
    from sqlite_cjk_fts import connect, create_table

    db = connect(":memory:")  # or your database path
    create_table(db, "docs", ["title", "content"])
    db.execute("INSERT INTO docs VALUES ('title', 'content')")
    results = db.execute("SELECT * FROM docs WHERE docs MATCH 'keyword'").fetchall()

Or use the Connection class directly for context manager support.

Tokenizer name: cjk_bigram
"""

import sqlite3
import sys
import os
from pathlib import Path
from typing import Optional, List, Union

__version__ = "1.0.0"
__all__ = ["connect", "create_table", "Connection", "Tokenizer", "enable_load_extension"]

Tokenizer = "cjk_bigram"
"""The tokenizer name to use in CREATE VIRTUAL TABLE statements."""


def _get_ext_path() -> str:
    """Locate the compiled extension for the current platform."""
    lib_dir = Path(__file__).parent / "_lib"
    ext_name = "libcjkfts"

    if sys.platform == "darwin":
        for name in [f"{ext_name}.dylib", f"{ext_name}.so"]:
            path = lib_dir / name
            if path.exists():
                return str(path)
    elif sys.platform == "linux":
        for name in [f"{ext_name}.so", f"{ext_name}.dylib"]:
            path = lib_dir / name
            if path.exists():
                return str(path)

    return ""


def enable_load_extension(conn: sqlite3.Connection) -> None:
    """
    Enable extension loading on the given connection.

    Note: Some Python sqlite3 builds (including Apple's pre-installed Python
    on macOS) do not support load_extension(). Use Homebrew Python or compile
    SQLite with JSON1/FTS5 enabled.
    """
    if hasattr(conn, "enable_load_extension"):
        conn.enable_load_extension(True)
    else:
        raise RuntimeError(
            "This Python's sqlite3 module does not support extension loading. "
            "On macOS, install Homebrew Python and use it instead: "
            "/opt/homebrew/bin/python3"
        )


class Connection(sqlite3.Connection):
    """
    Extended sqlite3.Connection that auto-loads the CJK tokenizer.

    Use via sqlite_cjk_fts.connect() factory function, or inherit from it
    if you need custom behavior.
    """

    def __init__(self, database: str, **kwargs):
        ext_path = _get_ext_path()
        if not ext_path:
            raise FileNotFoundError(
                "CJK FTS5 extension not found in package. "
                "Please rebuild: python -m pip install --no-binary :all: sqlite-cjk-fts"
            )
        super().__init__(database, **kwargs)
        enable_load_extension(self)
        self.load_extension(ext_path)


def connect(
    database: str,
    timeout: float = 5.0,
    detect_extensions: Optional[List[str]] = None,
    isolation_level: Optional[str] = None,
    check_same_thread: bool = True,
    factory: Optional[type] = None,
    cached_statements: int = 128,
    uri: bool = False,
) -> Connection:
    """
    Open a SQLite database and auto-load the CJK FTS5 tokenizer extension.

    Parameters
    ----------
    database : str
        Path to the database file, or ":memory:" for an in-memory database.
    timeout : float
        How long to wait for locks to be released (default 5.0 seconds).
    detect_extensions : list of str, optional
        Auto-detect extensions (not used by this package).
    isolation_level : str, optional
        Transaction isolation level.
    check_same_thread : bool
        If True (default), only the creating thread may use the connection.
    factory : type, optional
        Custom Connection factory (must be a subclass of sqlite3.Connection).
    cached_statements : int
        Number of prepared statements to cache (default 128).
    uri : bool
        If True, interpret database as a URI (default False).

    Returns
    -------
    Connection
        A sqlite3.Connection subclass with the CJK tokenizer loaded.

    Examples
    --------
    >>> from sqlite_cjk_fts import connect
    >>> db = connect(":memory:")
    >>> db.execute("CREATE VIRTUAL TABLE docs USING fts5(content, tokenize='cjk_bigram')")
    >>> db.execute("INSERT INTO docs VALUES ('測試', '中文內容')")
    >>> for row in db.execute("SELECT * FROM docs WHERE docs MATCH '中文'"):
    ...     print(row)
    """
    kwargs = {
        "timeout": timeout,
        "detect_extensions": detect_extensions,
        "isolation_level": isolation_level,
        "check_same_thread": check_same_thread,
        "cached_statements": cached_statements,
        "uri": uri,
    }
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if factory is None:
        factory = Connection

    kwargs["factory"] = factory

    return sqlite3.connect(database, **kwargs)


def create_table(
    conn: sqlite3.Connection,
    name: str,
    columns: List[str],
    tokenizer: str = Tokenizer,
    content_columns: Optional[List[str]] = None,
) -> None:
    """
    Create an FTS5 virtual table with the CJK bigram tokenizer.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection.
    name : str
        Table name.
    columns : list of str
        Column names for the FTS5 table.
    tokenizer : str
        Tokenizer name (default: "cjk_bigram").
    content_columns : list of str, optional
        Content columns for external content tables.

    Examples
    --------
    >>> from sqlite_cjk_fts import connect, create_table
    >>> db = connect(":memory:")
    >>> create_table(db, "docs", ["title", "body"])
    >>> db.execute("INSERT INTO docs VALUES ('天氣', '今天天氣很好')")
    >>> db.execute("SELECT * FROM docs WHERE docs MATCH '天氣'").fetchall()
    """
    if content_columns:
        col_def = ", ".join(content_columns)
        create_sql = f"""
        CREATE VIRTUAL TABLE {name} USING fts5(
            {", ".join(columns)},
            content={col_def},
            tokenize='{tokenizer}'
        )
        """
    else:
        create_sql = f"""
        CREATE VIRTUAL TABLE {name} USING fts5(
            {", ".join(columns)},
            tokenize='{tokenizer}'
        )
        """
    conn.execute(create_sql)


def insert(
    conn: sqlite3.Connection,
    table: str,
    values: Union[tuple, dict],
) -> sqlite3.Cursor:
    """
    Insert a row into an FTS5 table.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection.
    table : str
        Table name.
    values : tuple or dict
        Values to insert (positional or named).

    Returns
    -------
    sqlite3.Cursor
    """
    placeholders = ", ".join(["?"] * (len(values) if isinstance(values, tuple) else len(values)))
    if isinstance(values, dict):
        cols = ", ".join(values.keys())
        placeholders = ", ".join([f":{k}" for k in values.keys()])
        sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    else:
        sql = f"INSERT INTO {table} VALUES ({placeholders})"
    return conn.execute(sql, values)


def search(
    conn: sqlite3.Connection,
    table: str,
    query: str,
    columns: Optional[List[str]] = None,
    limit: int = 0,
) -> List[tuple]:
    """
    Search the FTS5 table and return matching rows.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection.
    table : str
        Table name.
    query : str
        FTS5 MATCH query string.
    columns : list of str, optional
        Specific columns to select (default: all).
    limit : int
        Maximum rows to return (0 = no limit).

    Returns
    -------
    list of tuple
        Matching rows.

    Examples
    --------
    >>> db = connect(":memory:")
    >>> create_table(db, "docs", ["title", "body"])
    >>> insert(db, "docs", ("天氣預報", "今天天氣非常好"))
    >>> search(db, "docs", "天氣")
    [('天氣預報', '今天天氣非常好')]
    """
    cols = ", ".join(columns) if columns else "*"
    sql = f"SELECT {cols} FROM {table} WHERE {table} MATCH ?"
    if limit > 0:
        sql += f" LIMIT {limit}"
    cur = conn.execute(sql, (query,))
    return cur.fetchall()