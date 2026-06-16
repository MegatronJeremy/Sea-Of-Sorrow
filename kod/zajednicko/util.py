"""
Zajedničke pomoćne funkcije: kodifikacija energetske klase, raspoređivanje
proizvoda u cenovne opsege, normalizacija/standardizacija (ručna implementacija,
bez sklearn-a — koristi se u zadacima 4/5/6) i izvoz rezultata u Excel.
"""
from __future__ import annotations

import math

import pandas as pd

# Redosled energetskih klasa od najlošije do najbolje (uključuje staru i novu
# EU klasifikaciju, jer sajtovi prodavnica koriste oba sistema).
ENERGETSKE_KLASE = [
    "G", "F", "E", "D", "C", "B", "A",
    "A+", "A++", "A+++",
]
ENERGETSKA_KLASA_NA_BROJ = {klasa: i + 1 for i, klasa in enumerate(ENERGETSKE_KLASE)}


def energetska_klasa_u_broj(klasa: str | None) -> int | None:
    """Mapira tekstualnu energetsku klasu u broj (G=1 ... A+++=10) za ML modele."""
    if not klasa:
        return None
    klasa = klasa.strip().upper()
    return ENERGETSKA_KLASA_NA_BROJ.get(klasa)


def cenovni_opseg(cena: float) -> str:
    """Vraća naziv cenovnog opsega za dati iznos (koristi se u zadatku 3)."""
    if cena <= 30_000:
        return "≤ 30.000"
    if cena <= 100_000:
        return "30.001–100.000"
    if cena <= 300_000:
        return "100.001–300.000"
    return "≥ 300.000"


def normalizuj(kolona: pd.Series) -> pd.Series:
    """Min-max normalizacija u [0, 1]. Ručna implementacija (bez sklearn-a)."""
    minimum, maksimum = kolona.min(), kolona.max()
    if maksimum == minimum:
        return kolona * 0.0
    return (kolona - minimum) / (maksimum - minimum)


def standardizuj(kolona: pd.Series) -> pd.Series:
    """Z-score standardizacija (srednja 0, std 1). Ručna implementacija."""
    sredina, std = kolona.mean(), kolona.std()
    if std == 0 or math.isnan(std):
        return kolona * 0.0
    return (kolona - sredina) / std


def sacuvaj_u_excel(podaci: dict[str, pd.DataFrame], putanja: str) -> None:
    """Snima više DataFrame-ova u jedan .xlsx fajl, svaki na svom sheet-u.

    Primer:
        sacuvaj_u_excel({"po_kategoriji": df1, "top_brendovi": df2}, "izvestaj/upiti.xlsx")
    """
    with pd.ExcelWriter(putanja, engine="xlsxwriter") as writer:
        for naziv_sheeta, df in podaci.items():
            df.to_excel(writer, sheet_name=naziv_sheeta[:31], index=False)
