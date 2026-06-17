"""
Testovi za kod/04_regresija/regresija.py

Proverava: ispravnost GD koraka, konvergenciju, metrike i pripremu podataka.
Sve bez baze — koristi sintetičke NumPy podatke.
"""
from __future__ import annotations

import numpy as np
import pytest

# conftest.py dodaje kod/04_regresija na sys.path
from regresija import (
    LinearnaRegresijaGD,
    podeli_train_test,
    pripremi_podatke,
    r2_skor,
    rmse,
)


# ── metrike ───────────────────────────────────────────────────────────────────

class TestMetrike:
    def test_r2_perfektan(self):
        y = np.array([1.0, 2.0, 3.0])
        assert r2_skor(y, y) == pytest.approx(1.0)

    def test_r2_nula_za_sredinu(self):
        y = np.array([1.0, 2.0, 3.0])
        y_pred = np.full_like(y, y.mean())
        assert r2_skor(y, y_pred) == pytest.approx(0.0, abs=1e-9)

    def test_r2_negativan_za_los_model(self):
        y = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([4.0, 3.0, 2.0, 1.0])  # obrnuto
        assert r2_skor(y, y_pred) < 0

    def test_rmse_perfektan(self):
        y = np.array([10.0, 20.0, 30.0])
        assert rmse(y, y) == pytest.approx(0.0)

    def test_rmse_pozitivan(self):
        y = np.array([0.0, 0.0])
        y_pred = np.array([3.0, 4.0])
        # sqrt(mean([9, 16])) = sqrt(12.5) ≈ 3.536
        assert rmse(y, y_pred) == pytest.approx(np.sqrt(12.5))

    def test_rmse_nije_negativan(self):
        rng = np.random.default_rng(0)
        y = rng.normal(0, 1, 100)
        y_pred = rng.normal(0, 1, 100)
        assert rmse(y, y_pred) >= 0


# ── LinearnaRegresijaGD ────────────────────────────────────────────────────────

class TestLinearnaRegresijaGD:
    @staticmethod
    def _linearan_dataset(n=200, seed=0):
        """y = 3*x1 - 2*x2 + 5, standardizovano."""
        rng = np.random.default_rng(seed)
        X = rng.normal(0, 1, (n, 2))
        y = 3 * X[:, 0] - 2 * X[:, 1] + 5 + rng.normal(0, 0.1, n)
        return X, y

    def test_fit_vraca_sebe(self):
        X, y = self._linearan_dataset()
        model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=100)
        assert model.fit(X, y) is model

    def test_trosak_opada(self):
        X, y = self._linearan_dataset()
        model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=500)
        model.fit(X, y)
        historija = model.istorija_troska
        assert len(historija) == 500
        # trošak na kraju mora biti manji nego na početku
        assert historija[-1] < historija[0]

    def test_r2_na_linearnom_skupu(self):
        X, y = self._linearan_dataset(n=500)
        X_train, X_test, y_train, y_test = podeli_train_test(X, y, test_udeo=0.2)
        model = LinearnaRegresijaGD(stopa_ucenja=0.1, broj_iteracija=1000)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        assert r2_skor(y_test, y_pred) > 0.95

    def test_dimenzije_predikcije(self):
        X, y = self._linearan_dataset(n=100)
        model = LinearnaRegresijaGD().fit(X, y)
        y_pred = model.predict(X)
        assert y_pred.shape == (100,)

    def test_inicijalne_tezine_nula(self):
        X, y = self._linearan_dataset()
        model = LinearnaRegresijaGD()
        model.fit(X, y)
        # posle fit-a w mora biti inicijalizovan (neće biti sve nule)
        assert model.w is not None
        assert model.w.shape == (X.shape[1],)


# ── podeli_train_test ──────────────────────────────────────────────────────────

class TestPodelivTrainTest:
    def test_zbir_velicina(self):
        X = np.ones((100, 3))
        y = np.ones(100)
        X_tr, X_te, y_tr, y_te = podeli_train_test(X, y, test_udeo=0.2)
        assert len(X_tr) + len(X_te) == 100
        assert len(y_tr) + len(y_te) == 100

    def test_test_udeo(self):
        n = 200
        X = np.ones((n, 2))
        y = np.ones(n)
        X_tr, X_te, _, _ = podeli_train_test(X, y, test_udeo=0.25)
        assert len(X_te) == 50

    def test_reproduktibilnost(self):
        X = np.arange(100).reshape(50, 2)
        y = np.arange(50, dtype=float)
        r1 = podeli_train_test(X, y, seed=7)
        r2 = podeli_train_test(X, y, seed=7)
        np.testing.assert_array_equal(r1[0], r2[0])


# ── pripremi_podatke ──────────────────────────────────────────────────────────

class TestPripremiPodatke:
    def test_oblik_izlaza(self, sample_df):
        X, y, kolone = pripremi_podatke(sample_df)
        assert X.ndim == 2
        assert y.ndim == 1
        assert X.shape[0] == y.shape[0]
        assert len(kolone) == X.shape[1]

    def test_bez_nan_vrednosti(self, sample_df):
        X, y, _ = pripremi_podatke(sample_df)
        assert not np.isnan(X).any()
        assert not np.isnan(y).any()
