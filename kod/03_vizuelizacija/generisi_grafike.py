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

IZLAZ_DIR = Path(__file__).resolve().parents[2] / "izvestaj" / "grafici"
IZLAZ_DIR.mkdir(parents=True, exist_ok=True)


def _bar_i_pie(serija: pd.Series, naslov: str, fajl_prefix: str, max_krisaka: int = 10):
    """Bar-chart + pie-chart za istu seriju (broj + procentualni odnos).

    Pita: sitne kategorije preko `max_krisaka` grupišu se u 'ostalo', imena idu u
    legendu (ne kao labele na kriškama), a procenat se ispisuje samo na kriškama
    >= 3%. Tako se tekst ne preklapa kad ima puno / vrlo sitnih kategorija
    (npr. energetska klasa ili cenovni opseg sa kriškama ispod 1%).
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    serija.plot(kind="bar", ax=ax, color="#4c72b0")
    ax.set_title(f"{naslov} — broj proizvoda")
    ax.set_ylabel("broj proizvoda")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(IZLAZ_DIR / f"{fajl_prefix}_broj.png", dpi=150)
    plt.close(fig)

    pita = serija.copy()
    if len(pita) > max_krisaka:
        glavne = pita.iloc[:max_krisaka]
        ostalo = float(pita.iloc[max_krisaka:].sum())
        pita = pd.concat([glavne, pd.Series({"ostalo": ostalo})])
    udeli = pita / pita.sum() * 100.0

    fig, ax = plt.subplots(figsize=(7, 6))
    wedges, _t, _a = ax.pie(
        pita.values, startangle=90, pctdistance=0.72,
        autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
        textprops=dict(fontsize=9),
    )
    ax.legend(wedges, [f"{ime}  {p:.1f}%" for ime, p in udeli.items()],
              loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=9, frameon=False)
    ax.set_title(f"{naslov} — procentualni odnos")
    ax.axis("equal")
    fig.savefig(IZLAZ_DIR / f"{fajl_prefix}_procenat.png", dpi=150, bbox_inches="tight")
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
    """Horizontalni box plot raspodele cena po kategorijama (>= min_zapisa zapisa),
    sortirano po medijani. Horizontalno + visina srazmerna broju kategorija da bi
    labele bile čitljive -- vertikalna varijanta je bila preširoka i zgnječena."""
    grupe = {
        kat: pod["cena"].dropna().values / 1000
        for kat, pod in df.groupby("kategorija")
        if len(pod) >= min_zapisa
    }
    if not grupe:
        return
    # sortiraj po medijani (rastuce) radi citljivosti
    grupe = dict(sorted(grupe.items(), key=lambda kv: float(pd.Series(kv[1]).median())))

    fig, ax = plt.subplots(figsize=(9, max(5, len(grupe) * 0.34)))
    ax.boxplot(list(grupe.values()), tick_labels=list(grupe.keys()),
               patch_artist=True, orientation="horizontal")
    ax.set_xlabel("Cena (hilj. RSD)")
    ax.set_title("Raspodela cena po kategoriji")
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
