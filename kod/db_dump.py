"""
Izvozi primarnu i revidiranu bazu u SQL fajlove (CREATE TABLE + INSERT redovi).
Za predaju: baza/primarna_dump.sql i baza/revidirana_dump.sql.

Ne zahteva `pg_dump` u PATH-u — koristi psycopg2 direktno.

Pokretanje:  python kod/db_dump.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from zajednicko.db import cursor

_ROOT = Path(__file__).resolve().parent.parent
_BAZA = _ROOT / "baza"

TABELE = {
    "proizvodi_primarna": ("01_schema_primarna.sql", "primarna_dump.sql"),
    "proizvodi_revidirana": ("02_schema_revidirana.sql", "revidirana_dump.sql"),
}


def _sql_vrednost(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    # tekst / json / datum -> escapuj apostrofe
    return "'" + str(v).replace("'", "''") + "'"


def dump_tabelu(tabela: str, schema_fajl: str, izlaz: str) -> int:
    with cursor() as cur:
        cur.execute(f"SELECT * FROM {tabela} ORDER BY id;")
        kolone = [d[0] for d in cur.description]
        redovi = cur.fetchall()

    delovi = [
        f"-- Dump tabele {tabela} ({len(redovi)} redova)\n",
        f"-- Šema: baza/{schema_fajl}\n\n",
        (_BAZA / schema_fajl).read_text(encoding="utf-8"),
        f"\n\nTRUNCATE TABLE {tabela} RESTART IDENTITY CASCADE;\n\n",
    ]
    kol_lista = ", ".join(kolone)
    for red in redovi:
        vrednosti = ", ".join(_sql_vrednost(v) for v in red)
        delovi.append(f"INSERT INTO {tabela} ({kol_lista}) VALUES ({vrednosti});\n")

    (_BAZA / izlaz).write_text("".join(delovi), encoding="utf-8")
    return len(redovi)


if __name__ == "__main__":
    for tabela, (schema_fajl, izlaz) in TABELE.items():
        n = dump_tabelu(tabela, schema_fajl, izlaz)
        print(f"OK  baza/{izlaz}  ({n} redova)")
