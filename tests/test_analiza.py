"""
Testovi za kod/02_analiza/cisti_podatke.py

Proverava logiku čišćenja i preprocesiranja — bez konekcije na bazu.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# conftest.py dodaje kod/ na sys.path
from zajednicko.util import energetska_klasa_u_broj

sys.path.insert(0, str(Path(__file__).parent.parent / "kod" / "02_analiza"))
from cisti_podatke import OBAVEZNE_KOLONE, DODATNE_KOLONE, MIN_DODATNIH_ATRIBUTA, ocisti


class TestOcisti:
    """Testovi za funkciju ocisti() iz cisti_podatke.py."""

    def _pravi_df(self, n: int = 20) -> pd.DataFrame:
        """Sintetički DataFrame koji prolazi sva filtriranja."""
        rng = np.random.default_rng(99)
        return pd.DataFrame({
            "id": range(1, n + 1),
            "url": [f"https://test.com/p/{i}" for i in range(1, n + 1)],
            "naziv": [f"Proizvod {i}" for i in range(1, n + 1)],
            "brend": rng.choice(["Samsung", "LG", "Bosch"], size=n),
            "kategorija": rng.choice(["frizider", "televizor"], size=n),
            "cena": rng.uniform(10_000, 150_000, size=n).round(2),
            "na_lageru": True,
            "energetska_klasa": rng.choice(["A", "B", "C", "D"], size=n),
            "dijagonala_inch": rng.uniform(32, 75, size=n).round(1),
            "kapacitet_kg": None,
            "zapremina_l": rng.uniform(100, 500, size=n).round(1),
            "snaga_w": None,
            "datum_preuzimanja": pd.Timestamp("2025-03-01"),
        })

    def test_prolaze_potpuni_zapisi(self):
        df = self._pravi_df(20)
        ociscen = ocisti(df.copy())
        assert len(ociscen) == 20

    def test_filtrira_bez_naziva(self):
        df = self._pravi_df(10)
        df.loc[0, "naziv"] = None
        ociscen = ocisti(df.copy())
        assert len(ociscen) == 9

    def test_filtrira_nultu_cenu(self):
        df = self._pravi_df(10)
        df.loc[1, "cena"] = 0
        ociscen = ocisti(df.copy())
        assert len(ociscen) == 9

    def test_filtrira_negativnu_cenu(self):
        df = self._pravi_df(10)
        df.loc[2, "cena"] = -100
        ociscen = ocisti(df.copy())
        assert len(ociscen) == 9

    def test_filtrira_zapis_bez_tehnickih_atributa(self):
        df = self._pravi_df(10)
        # obriši sve tehničke atribute za prvi zapis
        for kol in DODATNE_KOLONE:
            if kol in df.columns:
                df.loc[0, kol] = None
        ociscen = ocisti(df.copy())
        assert len(ociscen) == 9

    def test_uklanja_duplikate_po_url(self):
        df = self._pravi_df(10)
        # dupliraj prvi red sa istim URL-om ali kasnijim datumom
        duplikat = df.iloc[[0]].copy()
        duplikat["datum_preuzimanja"] = pd.Timestamp("2025-06-01")
        duplikat["cena"] = 99999.0
        df = pd.concat([df, duplikat], ignore_index=True)
        ociscen = ocisti(df.copy())
        assert len(ociscen) == 10
        # treba da ostane noviji (cena 99999)
        idx = ociscen[ociscen["url"] == df.loc[0, "url"]].index
        assert ociscen.loc[idx[0], "cena"] == pytest.approx(99999.0)

    def test_dodaje_energetska_klasa_num(self):
        df = self._pravi_df(5)
        ociscen = ocisti(df.copy())
        assert "energetska_klasa_num" in ociscen.columns

    def test_energetska_klasa_num_vrednosti(self):
        df = self._pravi_df(5)
        df["energetska_klasa"] = ["A", "B", "C", "D", "A"]
        ociscen = ocisti(df.copy())
        for _, red in ociscen.iterrows():
            ocekivano = energetska_klasa_u_broj(red["energetska_klasa"])
            stvarno = red["energetska_klasa_num"]
            if ocekivano is None:
                assert pd.isna(stvarno)
            else:
                assert int(stvarno) == ocekivano

    def test_prazni_df_vraca_prazni_df(self):
        df = pd.DataFrame(columns=["naziv", "brend", "kategorija", "cena",
                                   "datum_preuzimanja", "url"] + DODATNE_KOLONE)
        ociscen = ocisti(df)
        assert len(ociscen) == 0


class TestObavezneFunkcije:
    """Provera da su konstante i struktura analiza modula ispravni."""

    def test_obavezne_kolone_definisane(self):
        assert "naziv" in OBAVEZNE_KOLONE
        assert "brend" in OBAVEZNE_KOLONE
        assert "kategorija" in OBAVEZNE_KOLONE
        assert "cena" in OBAVEZNE_KOLONE

    def test_min_dodatnih_atributa_pozitivan(self):
        assert MIN_DODATNIH_ATRIBUTA >= 1

    def test_dodatne_kolone_sadrze_tehnicke(self):
        tehnicke = {"energetska_klasa", "dijagonala_inch", "kapacitet_kg",
                    "zapremina_l", "snaga_w"}
        assert tehnicke <= set(DODATNE_KOLONE)
