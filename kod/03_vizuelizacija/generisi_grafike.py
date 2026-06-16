"""
Zadatak 3: Vizuelizacija podataka iz revidirane baze.

Generiše 4 grafikona (broj/procentualni odnos po kategoriji, brendu,
cenovnom opsegu i energetskoj klasi) i čuva ih kao PNG u izvestaj/grafici/.

Pokretanje:
    cd kod/03_vizuelizacija
    python generisi_grafike.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.db import get_connection  # noqa: E402
from zajednicko.util import cenovni_opseg  # noqa: E402

IZLAZ_DIR = Path("../../izvestaj/grafici")
IZLAZ_DIR.mkdir(parents=True, exist_ok=True)


def _bar_i_pie(serija: pd.Series, naslov: str, fajl_prefix: str):
    """Pravi i bar-chart i pie-chart za istu seriju (broj + procentualni odnos)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    serija.plot(kind="bar", ax=ax, color="#4c72b0")
    ax.set_title(f"{naslov} — broj proizvoda")
    ax.set_ylabel("broj proizvoda")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(IZLAZ_DIR / f"{fajl_prefix}_broj.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(serija.values, labels=serija.index, autopct="%1.1f%%", startangle=90)
    ax.set_title(f"{naslov} — procentualni odnos")
    plt.tight_layout()
    fig.savefig(IZLAZ_DIR / f"{fajl_prefix}_procenat.png", dpi=150)
    plt.close(fig)


def graf_kategorije(df: pd.DataFrame):
    top10 = df["kategorija"].value_counts().head(10)
    _bar_i_pie(top10, "10 najzastupljenijih kategorija", "kategorije")


def graf_brendovi(df: pd.DataFrame, min_brendova: int = 5):
    top = df["brend"].value_counts().head(max(min_brendova, 10))
    _bar_i_pie(top, "Najzastupljeniji brendovi", "brendovi")


def graf_cenovni_opsezi(df: pd.DataFrame):
    opsezi = df["cena"].apply(cenovni_opseg).value_counts()
    redosled = ["≤ 30.000", "30.001–100.000", "100.001–300.000", "≥ 300.000"]
    opsezi = opsezi.reindex(redosled).fillna(0)
    _bar_i_pie(opsezi, "Proizvodi po cenovnom opsegu (RSD)", "cenovni_opsezi")


def graf_energetska_klasa(df: pd.DataFrame):
    klase = df["energetska_klasa"].dropna().value_counts()
    _bar_i_pie(klase, "Proizvodi po energetskoj klasi", "energetska_klasa")


if __name__ == "__main__":
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM proizvodi_revidirana;", conn)
    conn.close()

    graf_kategorije(df)
    graf_brendovi(df)
    graf_cenovni_opsezi(df)
    graf_energetska_klasa(df)

    print(f"Grafici sačuvani u {IZLAZ_DIR.resolve()}")
