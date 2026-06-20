"""
Zadatak 3: Vizuelizacija podataka iz revidirane baze.

Generiše 6 tipova grafikona i čuva ih kao PNG u izvestaj/grafici/:
  - bar + pie po kategoriji, brendu, cenovnom opsegu, energetskoj klasi
  - scatter: cena vs. zapremina (frižideri) i cena vs. dijagonala (televizori)
  - box plot: raspodela cena po kategoriji

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


def graf_scatter_cena_zapremina(df: pd.DataFrame):
    """Scatter plot: cena vs. zapremina (l) za frižidere i zamrzivače."""
    pod = df[df["kategorija"].isin(["frizider", "zamrzivac"])].dropna(
        subset=["zapremina_l", "cena"]
    )
    if pod.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    for kat, grupa in pod.groupby("kategorija"):
        ax.scatter(grupa["zapremina_l"], grupa["cena"] / 1000,
                   label=kat, alpha=0.6, s=30)
    ax.set_xlabel("Zapremina (l)")
    ax.set_ylabel("Cena (hilj. RSD)")
    ax.set_title("Cena vs. zapremina (frižideri / zamrzivači)")
    ax.legend()
    plt.tight_layout()
    fig.savefig(IZLAZ_DIR / "scatter_cena_zapremina.png", dpi=150)
    plt.close(fig)


def graf_scatter_cena_dijagonala(df: pd.DataFrame):
    """Scatter plot: cena vs. dijagonala (inch) za televizore."""
    pod = df[df["kategorija"] == "televizor"].dropna(subset=["dijagonala_inch", "cena"])
    if pod.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(pod["dijagonala_inch"], pod["cena"] / 1000,
               alpha=0.6, s=30, color="#dd8452")
    ax.set_xlabel('Dijagonala ekrana (inch)')
    ax.set_ylabel("Cena (hilj. RSD)")
    ax.set_title("Cena vs. dijagonala ekrana (televizori)")
    plt.tight_layout()
    fig.savefig(IZLAZ_DIR / "scatter_cena_dijagonala.png", dpi=150)
    plt.close(fig)


def graf_boxplot_cena_po_kategoriji(df: pd.DataFrame, min_zapisa: int = 10):
    """Box plot raspodele cena po kategorijama (samo kategorije sa >= min_zapisa)."""
    grupe = {
        kat: pod["cena"].dropna().values / 1000
        for kat, pod in df.groupby("kategorija")
        if len(pod) >= min_zapisa
    }
    if not grupe:
        return

    fig, ax = plt.subplots(figsize=(max(6, len(grupe) * 1.2), 5))
    ax.boxplot(list(grupe.values()), tick_labels=list(grupe.keys()), patch_artist=True)
    ax.set_ylabel("Cena (hilj. RSD)")
    ax.set_title("Raspodela cena po kategoriji")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(IZLAZ_DIR / "boxplot_cena_kategorija.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM proizvodi_revidirana;", conn)
    conn.close()

    graf_kategorije(df)
    graf_brendovi(df)
    graf_cenovni_opsezi(df)
    graf_energetska_klasa(df)
    graf_scatter_cena_zapremina(df)
    graf_scatter_cena_dijagonala(df)
    graf_boxplot_cena_po_kategoriji(df)

    print(f"Grafici sačuvani u {IZLAZ_DIR.resolve()}")
