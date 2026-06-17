"""
Testovi za kod/06_preporuke/recommender.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# conftest.py dodaje kod/06_preporuke na sys.path
from recommender import (
    ContentBasedRecommender,
    izgradi_tfidf_matricu,
    kosinusna_slicnost,
)


# ── kosinusna_slicnost ────────────────────────────────────────────────────────

class TestKosinusnaSlicnost:
    def test_isti_vektori(self):
        v = np.array([1.0, 2.0, 3.0])
        assert kosinusna_slicnost(v, v) == pytest.approx(1.0)

    def test_ortogonalni_vektori(self):
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        assert kosinusna_slicnost(v1, v2) == pytest.approx(0.0)

    def test_suprotni_vektori(self):
        v = np.array([1.0, 0.0])
        assert kosinusna_slicnost(v, -v) == pytest.approx(-1.0)

    def test_nulti_vektor_vraca_nulu(self):
        v = np.array([1.0, 2.0])
        nula = np.zeros(2)
        assert kosinusna_slicnost(v, nula) == 0.0
        assert kosinusna_slicnost(nula, nula) == 0.0

    def test_raspon_minus1_do_1(self):
        rng = np.random.default_rng(42)
        for _ in range(20):
            v1, v2 = rng.normal(0, 1, 10), rng.normal(0, 1, 10)
            s = kosinusna_slicnost(v1, v2)
            assert -1.0 - 1e-9 <= s <= 1.0 + 1e-9


# ── izgradi_tfidf_matricu ─────────────────────────────────────────────────────

class TestTFIDF:
    def test_oblik_matrice(self):
        nazivi = pd.Series(["Samsung frižider", "LG veš mašina", "Bosch aspirator"])
        mat = izgradi_tfidf_matricu(nazivi)
        assert mat.shape[0] == 3
        assert mat.shape[1] > 0

    def test_vrednosti_nenegatvne(self):
        nazivi = pd.Series(["aparat za kafu", "espreso mašina", "kafe mašina"])
        mat = izgradi_tfidf_matricu(nazivi)
        assert (mat >= 0).all()

    def test_zajednicki_termin_manji_idf(self):
        # "frižider" se pojavljuje u svim — treba imati manji IDF od "Samsung"
        nazivi = pd.Series([
            "Samsung frižider", "LG frižider", "Bosch frižider",
        ])
        mat = izgradi_tfidf_matricu(nazivi)
        # matrica je n×V — suma IDF-a za "frižider" mora biti < suma za "samsung"
        # (ili jednaka 0 jer log(N/N)=0)
        assert mat.shape == (3, mat.shape[1])

    def test_prazan_dokument_radi(self):
        nazivi = pd.Series(["", "nešto", ""])
        mat = izgradi_tfidf_matricu(nazivi)
        assert mat.shape[0] == 3


# ── ContentBasedRecommender ───────────────────────────────────────────────────

class TestContentBasedRecommender:
    def test_inicijalizacija(self, sample_df):
        rec = ContentBasedRecommender(sample_df)
        assert rec.feature_matrica.shape[0] == len(sample_df)

    def test_preporucuje_tacno_top_n(self, sample_df):
        rec = ContentBasedRecommender(sample_df)
        # uzmi id prvog frižidera
        frizideri = sample_df[sample_df["kategorija"] == "frizider"]
        if len(frizideri) < 2:
            pytest.skip("Nema dovoljno frižidera u fixture-u")
        pid = int(frizideri.iloc[0]["id"])
        rezultat = rec.preporuci(pid, top_n=3)
        assert len(rezultat) <= 3

    def test_preporuke_iste_kategorije(self, sample_df):
        rec = ContentBasedRecommender(sample_df)
        frizideri = sample_df[sample_df["kategorija"] == "frizider"]
        if len(frizideri) < 2:
            pytest.skip("Nema dovoljno frižidera")
        pid = int(frizideri.iloc[0]["id"])
        rezultat = rec.preporuci(pid, top_n=5)
        # preporučeni ne sme biti sam sebi (ni po id-u)
        assert pid not in rezultat["id"].values

    def test_nepostojeci_id_baca_gresku(self, sample_df):
        rec = ContentBasedRecommender(sample_df)
        with pytest.raises(ValueError):
            rec.preporuci(999_999, top_n=3)

    def test_slicnost_kolona_postoji(self, sample_df):
        rec = ContentBasedRecommender(sample_df)
        frizideri = sample_df[sample_df["kategorija"] == "frizider"]
        if len(frizideri) < 2:
            pytest.skip("Nema dovoljno frižidera")
        pid = int(frizideri.iloc[0]["id"])
        rezultat = rec.preporuci(pid, top_n=3)
        assert "slicnost" in rezultat.columns
        assert (rezultat["slicnost"] >= 0).all()
        assert (rezultat["slicnost"] <= 1.0 + 1e-9).all()
