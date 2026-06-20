"""
Izvršava upite iz upiti.sql (svaki odvojen praznim redom/komentarom sa brojem)
nad revidiranom bazom i izvozi rezultate u izvestaj/upiti_rezultati.xlsx
(jedan sheet po upitu).

Pokretanje:
    cd kod/02_analiza
    python izvezi_upite.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.db import get_connection  # noqa: E402
from zajednicko.util import sacuvaj_u_excel  # noqa: E402

NAZIVI_UPITA = [
    "broj_po_kategoriji",
    "top10_brendovi",
    "energ_klasa_C_ili_bolje",
    "cena_do_50000",
    "top30_televizori_cena",
    "statistike_cena_po_kategoriji",
    "procenat_klasa_A_po_kategoriji",
    "top10_brendovi_po_ceni",
    "dostupnost_po_kategoriji",
    "frizideri_po_velicini",
]


def ucitaj_upite(putanja: str) -> list[str]:
    tekst = Path(putanja).read_text(encoding="utf-8")
    blokovi = re.split(r"--\s*\d+\)", tekst)[1:]
    rezultat = []
    for blok in blokovi:
        # ukloni sve redove pre prvog SQL kljucne reci
        linije = blok.splitlines()
        sql_start = next(
            (i for i, l in enumerate(linije)
             if re.match(r"\s*(SELECT|WITH|INSERT|UPDATE|DELETE)", l, re.I)),
            0
        )
        sql = "\n".join(linije[sql_start:]).strip()
        if sql:
            rezultat.append(sql)
    return rezultat


if __name__ == "__main__":
    _DIR = Path(__file__).resolve().parent
    upiti = ucitaj_upite(_DIR / "upiti.sql")
    conn = get_connection()
    rezultati = {}
    for naziv, upit in zip(NAZIVI_UPITA, upiti):
        df = pd.read_sql_query(upit, conn)
        rezultati[naziv] = df
        print(f"{naziv}: {len(df)} redova")
    conn.close()

    _IZVESTAJ = _DIR.parents[1] / "izvestaj"
    _IZVESTAJ.mkdir(exist_ok=True)
    sacuvaj_u_excel(rezultati, str(_IZVESTAJ / "upiti_rezultati.xlsx"))
    print("Sačuvano u izvestaj/upiti_rezultati.xlsx")
