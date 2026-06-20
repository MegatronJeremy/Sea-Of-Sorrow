"""
Konekcija na SQLite bazu (bez eksternih zavisnosti — sqlite3 je deo Pythona).

Putanja do .db fajla se čita iz .env (DB_PATH), podrazumevano:
    <koren_projekta>/podaci/psz.db

Koristi se iz svih podfoldera:
    from zajednicko.db import get_connection, cursor, run_sql_file
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

DB_PATH = os.getenv("DB_PATH", str(_ROOT / "podaci" / "psz.db"))


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Otvara SQLite konekciju. Kreira fajl i direktorijum ako ne postoje."""
    path = db_path or DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row   # redovi se ponašaju kao rečnici
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def cursor(db_path: str | None = None, dict_cursor: bool = False):
    """Context manager koji otvara konekciju + kursor i commituje na izlazu.

    dict_cursor=True: fetchall/fetchone vraćaju obične dict-ove umesto Row objekata.

    Primer:
        with cursor() as cur:
            cur.execute("SELECT 1")
    """
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        if dict_cursor:
            _orig_fetchall = cur.fetchall
            _orig_fetchone = cur.fetchone
            cur.fetchall = lambda: [dict(r) for r in _orig_fetchall()]
            cur.fetchone = lambda: (lambda r: dict(r) if r else None)(_orig_fetchone())
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_sql_file(path: str, db_path: str | None = None) -> None:
    """Izvršava ceo .sql fajl (npr. šemu baze)."""
    sql = Path(path).read_text(encoding="utf-8")
    conn = get_connection(db_path)
    try:
        conn.executescript(sql)
    finally:
        conn.close()
