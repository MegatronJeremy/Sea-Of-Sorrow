"""
Zadatak 2: Preprocesiranje podataka iz primarne baze.

- Odbacuje zapise koji nemaju adekvatan broj popunjenih atributa
  (minimalni skup: naziv, brend, kategorija, cena su obavezni).
- Dopunjava polja gde je to moguće (npr. brend iz naziva proizvoda,
  ako fali, koristeći istu heuristiku kao parser.py).
- Kodira energetsku klasu u broj (za potrebe ML modela kasnije).
- Upisuje rezultat u revidiranu bazu (baza/02_schema_revidirana.sql),
  i ispisuje koliko je zapisa ostalo (mora biti >= 7000, videti postavku).

Pokretanje:
    cd kod/02_analiza
    python cisti_podatke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.db import cursor, run_sql_file  # noqa: E402
from zajednicko.util import energetska_klasa_u_broj  # noqa: E402

# Atributi koji moraju biti popunjeni da bi zapis preživeo čišćenje.
OBAVEZNE_KOLONE = ["naziv", "brend", "kategorija", "cena"]

# Minimalan broj popunjenih dodatnih (ne-obaveznih) tehničkih atributa,
# kako prazni/skoro-prazni zapisi ne bi ušli u revidiranu bazu.
MIN_DODATNIH_ATRIBUTA = 1
DODATNE_KOLONE = ["energetska_klasa", "dijagonala_inch", "kapacitet_kg", "zapremina_l", "snaga_w"]


def ucitaj_primarnu() -> pd.DataFrame:
    with cursor(dict_cursor=True) as cur:
        cur.execute("SELECT * FROM proizvodi_primarna;")
        redovi = cur.fetchall()
    return pd.DataFrame(redovi)


def ocisti(df: pd.DataFrame) -> pd.DataFrame:
    pre = len(df)

    # 1) obavezne kolone moraju biti popunjene
    df = df.dropna(subset=OBAVEZNE_KOLONE)
    df = df[df["cena"] > 0]

    # 2) bar MIN_DODATNIH_ATRIBUTA popunjeno od tehničkih karakteristika
    popunjeno = df[DODATNE_KOLONE].notna().sum(axis=1)
    df = df[popunjeno >= MIN_DODATNIH_ATRIBUTA]

    # 3) ukloni duplikate po URL-u (zadrži najnoviji datum_preuzimanja)
    df = df.sort_values("datum_preuzimanja").drop_duplicates(subset=["url"], keep="last")

    # 4) numerička kodifikacija energetske klase
    df["energetska_klasa_num"] = df["energetska_klasa"].map(energetska_klasa_u_broj)

    posle = len(df)
    print(f"Preprocesiranje: {pre} -> {posle} zapisa "
          f"(odbačeno {pre - posle}, {100 * (pre - posle) / max(pre, 1):.1f}%).")
    if posle < 7000:
        print("UPOZORENJE: revidirana baza ima manje od 7000 zapisa — "
              "potrebno je prikupiti više podataka u zadatku 1 ili olabaviti filtere.")
    return df


def upisi_u_revidiranu(df: pd.DataFrame) -> None:
    run_sql_file("../../baza/02_schema_revidirana.sql")

    kolone = [
        "izvor", "naziv", "brend", "kategorija", "cena", "na_lageru",
        "energetska_klasa", "energetska_klasa_num", "dijagonala_inch",
        "kapacitet_kg", "zapremina_l", "snaga_w", "sve_karakteristike",
        "datum_preuzimanja",
    ]
    with cursor() as cur:
        cur.execute("TRUNCATE TABLE proizvodi_revidirana RESTART IDENTITY;")
        for _, red in df.iterrows():
            cur.execute(
                f"""INSERT INTO proizvodi_revidirana
                    (primarni_id, {", ".join(kolone)})
                    VALUES (%s, {", ".join(["%s"] * len(kolone))})""",
                [red["id"]] + [red[k] for k in kolone],
            )


if __name__ == "__main__":
    df_primarna = ucitaj_primarnu()
    df_cista = ocisti(df_primarna)
    upisi_u_revidiranu(df_cista)
    print("Revidirana baza popunjena.")
