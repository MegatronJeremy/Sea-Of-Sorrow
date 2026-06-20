"""
Konekcija na PostgreSQL bazu.

Čita parametre konekcije iz .env fajla (vidi .env.example u korenu projekta).
Koristi se iz svih podfoldera (crawler, analiza, aplikacija) preko:

    from zajednicko.db import get_connection, cursor, run_sql_file
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

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


def je_auth_greska(e: Exception) -> bool:
    """True ako je izuzetak posledica pogrešne/nedostajuće lozinke."""
    msg = str(e).lower()
    return any(k in msg for k in ("password", "authentication", "lozink"))


def postavi_lozinku(pwd: str, sacuvaj: bool = True) -> None:
    """Postavlja lozinku za naredne konekcije (runtime) i opciono je upisuje u .env."""
    global DB_PASSWORD
    DB_PASSWORD = pwd
    if sacuvaj:
        _upisi_u_env("DB_PASSWORD", pwd)


def _upisi_u_env(kljuc: str, vrednost: str) -> None:
    """Ažurira (ili dodaje) jedan ključ u .env fajlu u korenu projekta."""
    env = _ROOT / ".env"
    linije = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    nadjeno = False
    for i, l in enumerate(linije):
        if l.strip().startswith(f"{kljuc}="):
            linije[i] = f"{kljuc}={vrednost}"
            nadjeno = True
            break
    if not nadjeno:
        linije.append(f"{kljuc}={vrednost}")
    env.write_text("\n".join(linije) + "\n", encoding="utf-8")


@contextmanager
def cursor(dbname: str | None = None, dict_cursor: bool = False):
    """Context manager koji otvara konekciju + kursor i commituje na izlazu.

    dict_cursor=True: redovi se vraćaju kao rečnici (RealDictCursor).

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


def kreiraj_bazu_ako_ne_postoji(dbname: str | None = None) -> bool:
    """Kreira bazu (CREATE DATABASE) ako ne postoji — povezuje se na sistemsku
    'postgres' bazu. Vraća True ako je baza upravo kreirana.

    Ovo zamenjuje `createdb` CLI komandu, pa nije potreban psql u PATH-u.
    """
    cilj = dbname or DB_NAME
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname="postgres",
        user=DB_USER, password=DB_PASSWORD,
    )
    try:
        conn.autocommit = True  # CREATE DATABASE ne sme u transakciji
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (cilj,))
            if cur.fetchone():
                return False
            cur.execute(f'CREATE DATABASE "{cilj}";')
            return True
    finally:
        conn.close()


def run_sql_file(path: str, dbname: str | None = None) -> None:
    """Izvršava ceo .sql fajl (npr. šemu baze) nad zadatom bazom."""
    sql = Path(path).read_text(encoding="utf-8")
    with cursor(dbname) as cur:
        cur.execute(sql)
