"""
Inicijalizacija PostgreSQL baze:
  1. kreira bazu (CREATE DATABASE) ako ne postoji — nije potreban `createdb` CLI
  2. pokreće obe šeme (primarna + revidirana tabela)

Pokretanje:  python kod/db_init.py
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import zajednicko.db as db
from zajednicko.db import DB_NAME, kreiraj_bazu_ako_ne_postoji, run_sql_file

_ROOT = Path(__file__).resolve().parent.parent


def _kreiraj_uz_prompt():
    """Kreira bazu; na pogrešnu lozinku traži je sa terminala (do 3 puta)."""
    for pokusaj in range(3):
        try:
            return kreiraj_bazu_ako_ne_postoji()
        except Exception as e:
            if not db.je_auth_greska(e):
                raise
            print(f"Pogrešna lozinka za korisnika '{db.DB_USER}'.")
            pwd = getpass.getpass("Unesi PostgreSQL lozinku: ")
            db.postavi_lozinku(pwd)  # čuva u .env za ubuduće
    return kreiraj_bazu_ako_ne_postoji()


# Tabele koje mogu da se napune iz dump-a (baza/*_dump.sql) ako su prazne.
_DUMPOVI = [
    ("proizvodi_primarna", "primarna_dump.sql"),
    ("proizvodi_revidirana", "revidirana_dump.sql"),
]


def _tabela_prazna(tabela: str) -> bool:
    with db.cursor() as cur:
        cur.execute(f"SELECT NOT EXISTS (SELECT 1 FROM {tabela} LIMIT 1);")
        return bool(cur.fetchone()[0])


try:
    kreirana = _kreiraj_uz_prompt()
    print(f"Baza '{DB_NAME}': {'kreirana' if kreirana else 'već postoji'}")
except Exception as e:
    print(f"GRESKA pri konekciji na PostgreSQL: {e}")
    print("Proveri da je PostgreSQL pokrenut (DB_HOST/DB_PORT u .env).")
    sys.exit(1)

run_sql_file(str(_ROOT / "baza" / "01_schema_primarna.sql"))
run_sql_file(str(_ROOT / "baza" / "02_schema_revidirana.sql"))
print(f"OK — tabele kreirane u bazi '{DB_NAME}'.")

# Auto-restore: ako je tabela prazna a dump postoji, ucitaj podatke iz dump-a.
# Tako projekat radi "iz kutije" na tudjem/skolskom racunaru (bez skrejpovanja).
# Dump je "CREATE TABLE IF NOT EXISTS + INSERT", pa se bezbedno pusta posle seme.
for _tabela, _dump_fajl in _DUMPOVI:
    _dump = _ROOT / "baza" / _dump_fajl
    if not _dump.exists():
        continue
    if _tabela_prazna(_tabela):
        run_sql_file(str(_dump))
        with db.cursor() as _cur:
            _cur.execute(f"SELECT COUNT(*) FROM {_tabela};")
            _n = _cur.fetchone()[0]
        print(f"Ucitan dump -> {_tabela}: {_n} redova (iz baza/{_dump_fajl}).")
    else:
        print(f"{_tabela}: vec ima podatke — preskacem dump.")
