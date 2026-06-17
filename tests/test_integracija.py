"""
Integracioni testovi — testiraju kompletne pipeline od podataka do rezultata,
bez konekcije na bazu. Simuliraju tipičan tok rada:

  DataFrame (mock baza) -> cisti_podatke -> regresija/kmeans/recommender -> rezultati

Ovi testovi su namerno sporiji od jediničnih testova (nekoliko sekundi ukupno)
jer pokreću pun trening modela. Idealni su za CI/CD pre pusha.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# Mokujem psycopg2 pre importa koji ga zahtevaju
for _mod in ("psycopg2", "psycopg2.extras"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

_KOD = Path(__file__).parent.parent / "kod"
for _d in (_KOD, _KOD / "01_crawler", _KOD / "02_analiza",
           _KOD / "04_regresija", _KOD / "05_klasterovanje", _KOD / "06_preporuke"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from cisti_podatke import ocisti
from kmeans import KMeans, silhouette_score_rucno
from recommender import ContentBasedRecommender
from regresija import (
    LinearnaRegresijaGD,
    podeli_train_test,
    pripremi_podatke,
    r2_skor,
    rmse,
)
from zajednicko.util import cenovni_opseg, energetska_klasa_u_broj, normalizuj


# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def df_revidirana() -> pd.DataFrame:
    """Sintetička revidirana baza sa 200 zapisa i realnom raspodjelom atributa."""
    rng = np.random.default_rng(7)
    n = 200
    kategorije = rng.choice(
        ["frizider", "televizor", "ves_masina", "masina_za_sudove", "sporet"],
        size=n,
        p=[0.30, 0.25, 0.20, 0.15, 0.10],
    )
    brendovi = rng.choice(
        ["Samsung", "LG", "Bosch", "Philips", "Gorenje", "Whirlpool", "Beko"],
        size=n,
    )
    energ_klase = rng.choice(["A", "B", "C", "D", "E", None], size=n,
                              p=[0.20, 0.25, 0.20, 0.15, 0.10, 0.10])

    def cena_za(kat, i):
        baze = {"frizider": 70_000, "televizor": 80_000, "ves_masina": 55_000,
                "masina_za_sudove": 65_000, "sporet": 50_000}
        return max(15_000, rng.normal(baze.get(kat, 60_000), 25_000))

    return pd.DataFrame({
        "id": np.arange(1, n + 1),
        "naziv": [f"{b} {k} Model-{i}" for i, (b, k) in enumerate(zip(brendovi, kategorije))],
        "brend": brendovi,
        "kategorija": kategorije,
        "cena": [cena_za(k, i) for i, k in enumerate(kategorije)],
        "na_lageru": rng.choice([True, False], size=n, p=[0.75, 0.25]),
        "url": [f"https://test.rs/p/{i}" for i in range(n)],
        "energetska_klasa": energ_klase,
        "energetska_klasa_num": [energetska_klasa_u_broj(k) for k in energ_klase],
        "dijagonala_inch": pd.array(
            np.where(kategorije == "televizor", rng.uniform(32, 75, n).round(1), np.nan),
            dtype="Float64"),
        "kapacitet_kg": pd.array(
            np.where(kategorije == "ves_masina", rng.uniform(5, 12, n).round(1), np.nan),
            dtype="Float64"),
        "zapremina_l": pd.array(
            np.where(np.isin(kategorije, ["frizider", "sporet"]),
                     rng.uniform(100, 700, n).round(1), np.nan),
            dtype="Float64"),
        "snaga_w": pd.array(rng.choice([500.0, 1000.0, 2000.0, np.nan], size=n), dtype="Float64"),
        "datum_preuzimanja": pd.Timestamp("2025-03-15"),
        "sve_karakteristike": [{}] * n,
    })


# ── Pipeline: cisti_podatke -> ML ─────────────────────────────────────────────

class TestPipelineRegresija:
    def test_ocisti_ne_gubi_previse_zapisa(self, df_revidirana):
        ociscen = ocisti(df_revidirana.copy())
        assert len(ociscen) >= int(len(df_revidirana) * 0.7), \
            "ocisti() odbacuje previše zapisa na sintetičkim podacima"

    def test_priprema_i_trening(self, df_revidirana):
        X, y, kolone = pripremi_podatke(df_revidirana)
        assert X.shape[0] == y.shape[0]
        assert not np.isnan(X).any()
        assert len(kolone) == X.shape[1]

    def test_model_konvergira(self, df_revidirana):
        X, y, _ = pripremi_podatke(df_revidirana)
        X_tr, X_te, y_tr, y_te = podeli_train_test(X, y)
        model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=500).fit(X_tr, y_tr)
        # trošak mora opadati
        assert model.istorija_troska[-1] < model.istorija_troska[0]

    def test_r2_na_sintetickim_podacima(self, df_revidirana):
        X, y, _ = pripremi_podatke(df_revidirana)
        X_tr, X_te, y_tr, y_te = podeli_train_test(X, y)
        model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=1000).fit(X_tr, y_tr)
        r2 = r2_skor(y_te, model.predict(X_te))
        # R² na sintetičkim podacima sa šumom — čak i loš model mora biti > -1
        assert r2 > -1.0

    def test_rmse_pozitivan(self, df_revidirana):
        X, y, _ = pripremi_podatke(df_revidirana)
        X_tr, X_te, y_tr, y_te = podeli_train_test(X, y)
        model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=200).fit(X_tr, y_tr)
        assert rmse(y_te, model.predict(X_te)) > 0


# ── Pipeline: cisti_podatke -> KMeans ─────────────────────────────────────────

class TestPipelineKMeans:
    def test_klasterovanje_daje_k_klastera(self, df_revidirana):
        df = df_revidirana.dropna(subset=["cena", "energetska_klasa_num"]).copy()
        X = np.column_stack([
            normalizuj(df["cena"]),
            normalizuj(df["energetska_klasa_num"].astype(float)),
        ])
        k = 3
        model = KMeans(k=k).fit(X)
        assert len(np.unique(model.labele)) == k

    def test_silhouette_u_rasponu(self, df_revidirana):
        df = df_revidirana.dropna(subset=["cena", "energetska_klasa_num"]).copy()
        X = np.column_stack([normalizuj(df["cena"]),
                             normalizuj(df["energetska_klasa_num"].astype(float))])
        model = KMeans(k=3).fit(X)
        s = silhouette_score_rucno(X, model.labele)
        assert -1.0 <= s <= 1.0


# ── Pipeline: cisti_podatke -> Recommender ────────────────────────────────────

class TestPipelineRecommender:
    def test_preporuke_unutar_kategorije(self, df_revidirana):
        rec = ContentBasedRecommender(df_revidirana)
        # izaberi id frižidera
        frizideri = df_revidirana[df_revidirana["kategorija"] == "frizider"]
        pid = int(frizideri.iloc[0]["id"])
        rezultat = rec.preporuci(pid, top_n=5)
        # proveravamo da NI JEDAN preporučeni nije iz druge kategorije
        indeksi = rezultat.index.tolist()
        preporucene_kategorije = df_revidirana.loc[
            df_revidirana["id"].isin(rezultat["id"]), "kategorija"
        ].unique()
        assert list(preporucene_kategorije) == ["frizider"], \
            f"Preporuke moraju biti iste kategorije, dobijeno: {preporucene_kategorije}"

    def test_slicnost_opada(self, df_revidirana):
        rec = ContentBasedRecommender(df_revidirana)
        frizideri = df_revidirana[df_revidirana["kategorija"] == "frizider"]
        pid = int(frizideri.iloc[0]["id"])
        rezultat = rec.preporuci(pid, top_n=5)
        slicnosti = rezultat["slicnost"].tolist()
        # sličnosti moraju biti sortirane opadajuće
        assert slicnosti == sorted(slicnosti, reverse=True), \
            f"Preporuke nisu sortirane po sličnosti: {slicnosti}"


# ── Util pipeline ──────────────────────────────────────────────────────────────

class TestUtilPipeline:
    def test_cenovni_opseg_za_sve_cene(self, df_revidirana):
        opsezi = df_revidirana["cena"].apply(cenovni_opseg)
        assert opsezi.notna().all()
        ocekivani = {"≤ 30.000", "30.001–100.000", "100.001–300.000", "≥ 300.000"}
        assert set(opsezi.unique()) <= ocekivani

    def test_energetska_klasa_num_konzistentna(self, df_revidirana):
        for _, red in df_revidirana.iterrows():
            ocekivano = energetska_klasa_u_broj(red["energetska_klasa"])
            stvarno = red["energetska_klasa_num"]
            if ocekivano is None:
                assert stvarno is None or pd.isna(stvarno)
            else:
                assert int(stvarno) == ocekivano
