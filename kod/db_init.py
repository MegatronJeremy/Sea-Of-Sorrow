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
