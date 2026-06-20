"""
Inicijalizacija PostgreSQL baze:
  1. kreira bazu (CREATE DATABASE) ako ne postoji — nije potreban `createdb` CLI
  2. pokreće obe šeme (primarna + revidirana tabela)

Pokretanje:  python kod/db_init.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from zajednicko.db import DB_NAME, kreiraj_bazu_ako_ne_postoji, run_sql_file

_ROOT = Path(__file__).resolve().parent.parent

try:
    kreirana = kreiraj_bazu_ako_ne_postoji()
    print(f"Baza '{DB_NAME}': {'kreirana' if kreirana else 'već postoji'}")
except Exception as e:
    print(f"GRESKA pri konekciji na PostgreSQL: {e}")
    print("Proveri da je PostgreSQL pokrenut i da su DB_USER/DB_PASSWORD u .env tačni.")
    sys.exit(1)

run_sql_file(str(_ROOT / "baza" / "01_schema_primarna.sql"))
run_sql_file(str(_ROOT / "baza" / "02_schema_revidirana.sql"))
print(f"OK — tabele kreirane u bazi '{DB_NAME}'.")
