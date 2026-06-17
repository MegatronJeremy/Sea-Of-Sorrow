"""
Testovi za kod/05_klasterovanje/kmeans.py
"""
from __future__ import annotations

import numpy as np
import pytest

# conftest.py dodaje kod/05_klasterovanje na sys.path
from kmeans import KMeans, interpretiraj_klaster, silhouette_score_rucno


# ── KMeans ────────────────────────────────────────────────────────────────────

class TestKMeans:
    @staticmethod
    def _blobs(k=3, n_po_klasteru=50, seed=0):
        """Pravi jasno odvojene klastere."""
        rng = np.random.default_rng(seed)
        centri = np.array([[0, 0], [10, 0], [5, 8]], dtype=float)[:k]
        delovi = [rng.normal(c, 0.5, (n_po_klasteru, 2)) for c in centri]
        return np.vstack(delovi)

    def test_fit_vraca_sebe(self):
        X = self._blobs()
        model = KMeans(k=3)
        assert model.fit(X) is model

    def test_broj_jedinstvenih_labela(self):
        X = self._blobs(k=3)
        model = KMeans(k=3).fit(X)
        assert len(np.unique(model.labele)) == 3

    def test_duzina_labela(self):
        X = self._blobs(k=3, n_po_klasteru=40)
        model = KMeans(k=3).fit(X)
        assert len(model.labele) == X.shape[0]

    def test_oblik_centroida(self):
        X = self._blobs(k=3)
        model = KMeans(k=3).fit(X)
        assert model.centroidi.shape == (3, 2)

    def test_predict_konzistentan_sa_fit(self):
        X = self._blobs(k=3)
        model = KMeans(k=3).fit(X)
        pred = model.predict(X)
        # predict i labele moraju biti isti
        np.testing.assert_array_equal(pred, model.labele)

    def test_jasni_klasteri_tacni(self):
        X = self._blobs(k=2, n_po_klasteru=100)
        model = KMeans(k=2).fit(X)
        # svaka polovina mora biti u istom klasteru
        prvih_100 = model.labele[:100]
        drugih_100 = model.labele[100:]
        assert len(np.unique(prvih_100)) == 1
        assert len(np.unique(drugih_100)) == 1
        assert prvih_100[0] != drugih_100[0]

    def test_k_1_radi(self):
        X = np.random.default_rng(0).normal(0, 1, (20, 2))
        model = KMeans(k=1).fit(X)
        assert (model.labele == 0).all()


# ── silhouette_score_rucno ────────────────────────────────────────────────────

class TestSilhouetteScore:
    def test_raspon_minus1_do_1(self):
        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (50, 2))
        labele = KMeans(k=3).fit(X).labele
        s = silhouette_score_rucno(X, labele)
        assert -1.0 <= s <= 1.0

    def test_jasni_klasteri_visok_skor(self):
        X = np.vstack([
            np.random.default_rng(0).normal([0, 0], 0.1, (30, 2)),
            np.random.default_rng(1).normal([10, 10], 0.1, (30, 2)),
        ])
        labele = np.array([0] * 30 + [1] * 30)
        s = silhouette_score_rucno(X, labele)
        assert s > 0.9

    def test_jedan_klaster_vraca_nulu(self):
        X = np.random.default_rng(0).normal(0, 1, (20, 2))
        labele = np.zeros(20, dtype=int)
        assert silhouette_score_rucno(X, labele) == 0.0


# ── interpretiraj_klaster ─────────────────────────────────────────────────────

class TestInterpretirajKlaster:
    def test_sadrzi_cenu(self, sample_df):
        df_k = sample_df[sample_df["kategorija"] == "frizider"].copy()
        df_k["klaster"] = 0
        tekst = interpretiraj_klaster(df_k, ["cena"])
        assert "RSD" in tekst or "cena" in tekst.lower()
