"""
Konekcija na PostgreSQL bazu.

Čita parametre konekcije iz .env fajla (vidi .env.example u korenu projekta).
Koristi se iz svih podfoldera (crawler, analiza, aplikacija) preko:

    from zajednicko.db import get_connection
"""
import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Učitaj .env iz korena projekta (PSZ_Projekat/.env), bez obzira odakle se pokreće skripta.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(_ROOT, ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "psz_primarna")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_connection(dbname: str | None = None):
    """Vraća novu psycopg2 konekciju. Po default-u koristi DB_NAME iz .env."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=dbname or DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


@contextmanager
def cursor(dbname: str | None = None, dict_cursor: bool = False):
    """Context manager koji otvara konekciju + kursor i commituje na izlazu.

    Primer:
        with cursor() as cur:
            cur.execute("SELECT 1")
    """
    conn = get_connection(dbname)
    try:
        cur_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=cur_factory)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_sql_file(path: str, dbname: str | None = None) -> None:
    """Izvršava ceo .sql fajl (npr. šemu baze) nad zadatom bazom."""
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    with cursor(dbname) as cur:
        cur.execute(sql)
