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
    # upiti su razdvojeni linijama komentara koje počinju sa "-- N)"
    blokovi = re.split(r"-- \d+\)", tekst)[1:]  # prvi je prazan/uvodni komentar
    return [b.strip() for b in blokovi]


if __name__ == "__main__":
    upiti = ucitaj_upite("upiti.sql")
    conn = get_connection()
    rezultati = {}
    for naziv, upit in zip(NAZIVI_UPITA, upiti):
        df = pd.read_sql_query(upit, conn)
        rezultati[naziv] = df
        print(f"{naziv}: {len(df)} redova")
    conn.close()

    Path("../../izvestaj").mkdir(exist_ok=True)
    sacuvaj_u_excel(rezultati, "../../izvestaj/upiti_rezultati.xlsx")
    print("Sačuvano u izvestaj/upiti_rezultati.xlsx")
