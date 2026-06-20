"""
Zadatak 2: Preprocesiranje podataka iz primarne baze.

- Odbacuje zapise koji nemaju adekvatan broj popunjenih atributa
  (minimalni skup: naziv, brend, kategorija, cena su obavezni).
- Kodira energetsku klasu u broj (za potrebe ML modela).
- Upisuje rezultat u revidiranu bazu i ispisuje koliko je zapisa ostalo
  (mora biti >= 7000, videti postavku).

Pokretanje:
    cd kod/02_analiza
    python cisti_podatke.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.db import cursor, get_connection, run_sql_file  # noqa: E402
from zajednicko.util import energetska_klasa_u_broj  # noqa: E402

OBAVEZNE_KOLONE = ["naziv", "brend", "kategorija", "cena"]

MIN_DODATNIH_ATRIBUTA = 1
DODATNE_KOLONE = ["energetska_klasa", "dijagonala_inch", "kapacitet_kg", "zapremina_l", "snaga_w"]

_BAZA_DIR = Path(__file__).resolve().parents[2] / "baza"


def ucitaj_primarnu() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM proizvodi_primarna;", conn)
    conn.close()
    if "sve_karakteristike" in df.columns:
        df["sve_karakteristike"] = df["sve_karakteristike"].apply(
            lambda v: json.loads(v) if isinstance(v, str) else (v or {})
        )
    return df


def ocisti(df: pd.DataFrame) -> pd.DataFrame:
    pre = len(df)

    df = df.dropna(subset=OBAVEZNE_KOLONE)
    df = df[df["cena"] > 0]

    popunjeno = df[DODATNE_KOLONE].notna().sum(axis=1)
    df = df[popunjeno >= MIN_DODATNIH_ATRIBUTA]

    df = df.sort_values("datum_preuzimanja").drop_duplicates(subset=["url"], keep="last")

    df["energetska_klasa_num"] = df["energetska_klasa"].map(energetska_klasa_u_broj)

    posle = len(df)
    print(f"Preprocesiranje: {pre} -> {posle} zapisa "
          f"(odbaceno {pre - posle}, {100 * (pre - posle) / max(pre, 1):.1f}%).")
    if posle < 7000:
        print("UPOZORENJE: revidirana baza ima manje od 7000 zapisa.")
    return df


def upisi_u_revidiranu(df: pd.DataFrame) -> None:
    run_sql_file(str(_BAZA_DIR / "02_schema_revidirana.sql"))

    kolone = [
        "izvor", "naziv", "brend", "kategorija", "cena", "na_lageru",
        "energetska_klasa", "energetska_klasa_num", "dijagonala_inch",
        "kapacitet_kg", "zapremina_l", "snaga_w", "sve_karakteristike",
        "datum_preuzimanja",
    ]
    placeholder = ", ".join(["?"] * (len(kolone) + 1))
    sql = f"""INSERT INTO proizvodi_revidirana
              (primarni_id, {", ".join(kolone)})
              VALUES ({placeholder})"""

    with cursor() as cur:
        cur.execute("DELETE FROM proizvodi_revidirana;")
        for _, red in df.iterrows():
            vrednosti = [red.get("id")]
            for k in kolone:
                v = red.get(k)
                if k == "sve_karakteristike" and isinstance(v, dict):
                    v = json.dumps(v, ensure_ascii=False)
                elif hasattr(v, "item"):
                    v = v.item()
                elif not isinstance(v, (dict, list)) and pd.isna(v):
                    v = None
                vrednosti.append(v)
            cur.execute(sql, vrednosti)


if __name__ == "__main__":
    df_primarna = ucitaj_primarnu()
    df_cista = ocisti(df_primarna)
    upisi_u_revidiranu(df_cista)
    print("Revidirana baza popunjena.")
