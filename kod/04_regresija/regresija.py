"""
Zadatak 4: Višestruka linearna regresija — ručna implementacija
(funkcija troška, korak gradijentnog spusta i predikcija su samostalno
kodirani; sklearn se koristi ISKLJUČIVO za verifikaciju u zasebnoj funkciji).

Ciljna promenljiva: cena proizvoda.
Ulazni atributi (features): kategorija i brend (one-hot enkodirani),
energetska_klasa_num, dijagonala_inch, kapacitet_kg, zapremina_l, snaga_w.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class LinearnaRegresijaGD:
    """Višestruka linearna regresija obučena gradijentnim spustom (batch GD).

    Model: y_hat = X @ w + b
    Funkcija troška: srednja kvadratna greška (MSE).
    """

    def __init__(self, stopa_ucenja: float = 0.01, broj_iteracija: int = 1000):
        self.stopa_ucenja = stopa_ucenja
        self.broj_iteracija = broj_iteracija
        self.w: np.ndarray | None = None
        self.b: float = 0.0
        self.istorija_troska: list[float] = []

    def _trosak(self, X: np.ndarray, y: np.ndarray) -> float:
        """Funkcija troška: MSE = (1/2n) * sum((y_hat - y)^2)."""
        n = X.shape[0]
        y_hat = X @ self.w + self.b
        return float(np.sum((y_hat - y) ** 2) / (2 * n))

    def _korak_gradijentnog_spusta(self, X: np.ndarray, y: np.ndarray) -> None:
        """Jedan korak batch gradijentnog spusta: ažurira self.w i self.b."""
        n = X.shape[0]
        y_hat = X @ self.w + self.b
        greska = y_hat - y

        dw = (X.T @ greska) / n          # gradijent po težinama
        db = float(np.sum(greska) / n)   # gradijent po bias-u

        self.w -= self.stopa_ucenja * dw
        self.b -= self.stopa_ucenja * db

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearnaRegresijaGD":
        n, m = X.shape
        self.w = np.zeros(m)
        self.b = 0.0
        self.istorija_troska = []

        for _ in range(self.broj_iteracija):
            self._korak_gradijentnog_spusta(X, y)
            self.istorija_troska.append(self._trosak(X, y))

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predikcija: y_hat = X @ w + b."""
        return X @ self.w + self.b


# --- Metrike (ručna implementacija, koristi se za evaluaciju u izveštaju) ---

def r2_skor(y_stvarno: np.ndarray, y_predikcija: np.ndarray) -> float:
    ss_res = np.sum((y_stvarno - y_predikcija) ** 2)
    ss_tot = np.sum((y_stvarno - np.mean(y_stvarno)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else 0.0


def rmse(y_stvarno: np.ndarray, y_predikcija: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_stvarno - y_predikcija) ** 2)))


# --- Priprema podataka ---

def pripremi_podatke(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """One-hot enkodira kategoriju/brend, standardizuje numeričke kolone,
    i vraća (X, y, nazivi_kolona)."""
    df = df.dropna(subset=["cena"]).copy()

    numericke = ["energetska_klasa_num", "dijagonala_inch", "kapacitet_kg", "zapremina_l", "snaga_w"]
    for kol in numericke:
        df[kol] = df[kol].fillna(df[kol].median())
        df[kol] = (df[kol] - df[kol].mean()) / df[kol].std()  # standardizacija

    one_hot = pd.get_dummies(df[["kategorija", "brend"]], drop_first=True)

    X = pd.concat([df[numericke], one_hot], axis=1)
    y = df["cena"].values.astype(float)

    return X.values.astype(float), y, list(X.columns)


def podeli_train_test(X: np.ndarray, y: np.ndarray, test_udeo: float = 0.2, seed: int = 42):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    indeksi = rng.permutation(n)
    granica = int(n * (1 - test_udeo))
    train_idx, test_idx = indeksi[:granica], indeksi[granica:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from zajednicko.db import get_connection  # noqa: E402

    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM proizvodi_revidirana;", conn)
    conn.close()

    X, y, kolone = pripremi_podatke(df)
    X_train, X_test, y_train, y_test = podeli_train_test(X, y)

    model = LinearnaRegresijaGD(stopa_ucenja=0.05, broj_iteracija=2000)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"R2 skor (test):  {r2_skor(y_test, y_pred):.4f}")
    print(f"RMSE (test):     {rmse(y_test, y_pred):,.0f} RSD")
    print(f"Trošak na poslednjoj iteraciji: {model.istorija_troska[-1]:,.0f}")
