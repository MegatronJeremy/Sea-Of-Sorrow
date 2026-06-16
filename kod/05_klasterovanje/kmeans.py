"""
Zadatak 5: K-means klasterovanje — ručna implementacija (bez sklearn-a za
sam algoritam; sklearn.cluster.KMeans se može koristiti samo za verifikaciju).

Korisnik (kroz GUI u aplikaciji/) bira:
  - koje numeričke promenljive ulaze u analizu
  - težinski udeo svake promenljive (zbir = 100%)
  - broj klastera K

Standardizacija/normalizacija ulaznih promenljivih je obavezna pre
klasterovanja — videti zajednicko/util.py (normalizuj / standardizuj).
"""
from __future__ import annotations

import numpy as np


class KMeans:
    def __init__(self, k: int, max_iteracija: int = 300, tolerancija: float = 1e-4, seed: int = 42):
        self.k = k
        self.max_iteracija = max_iteracija
        self.tolerancija = tolerancija
        self.seed = seed
        self.centroidi: np.ndarray | None = None
        self.labele: np.ndarray | None = None

    def _inicijalizuj_centroide(self, X: np.ndarray) -> np.ndarray:
        """K-means++ inicijalizacija (bolja konvergencija od čisto nasumične)."""
        rng = np.random.default_rng(self.seed)
        n = X.shape[0]
        centroidi = [X[rng.integers(n)]]

        for _ in range(1, self.k):
            udaljenosti = np.array([
                min(np.sum((tacka - c) ** 2) for c in centroidi) for tacka in X
            ])
            verovatnoce = udaljenosti / udaljenosti.sum()
            sledeci = rng.choice(n, p=verovatnoce)
            centroidi.append(X[sledeci])

        return np.array(centroidi)

    @staticmethod
    def _dodeli_klastere(X: np.ndarray, centroidi: np.ndarray) -> np.ndarray:
        """Za svaku tačku, indeks najbližeg centroida (Euklidska udaljenost)."""
        udaljenosti = np.array([
            np.sum((X - c) ** 2, axis=1) for c in centroidi
        ])  # shape: (k, n)
        return np.argmin(udaljenosti, axis=0)

    def fit(self, X: np.ndarray) -> "KMeans":
        self.centroidi = self._inicijalizuj_centroide(X)

        for _ in range(self.max_iteracija):
            labele = self._dodeli_klastere(X, self.centroidi)

            novi_centroidi = np.array([
                X[labele == i].mean(axis=0) if np.any(labele == i) else self.centroidi[i]
                for i in range(self.k)
            ])

            pomeraj = np.sum((novi_centroidi - self.centroidi) ** 2)
            self.centroidi = novi_centroidi
            if pomeraj < self.tolerancija:
                break

        self.labele = self._dodeli_klastere(X, self.centroidi)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._dodeli_klastere(X, self.centroidi)


def silhouette_score_rucno(X: np.ndarray, labele: np.ndarray) -> float:
    """Ručna implementacija silhouette score-a (prosek po svim tačkama).

    s(i) = (b(i) - a(i)) / max(a(i), b(i))
      a(i) = prosečna udaljenost tačke i do ostalih tačaka u istom klasteru
      b(i) = najmanja prosečna udaljenost tačke i do tačaka u nekom DRUGOM klasteru
    """
    n = X.shape[0]
    klasteri = np.unique(labele)
    if len(klasteri) < 2:
        return 0.0

    skorovi = np.zeros(n)
    for i in range(n):
        sopstveni = labele[i]
        a_i = _prosecna_udaljenost(X, i, labele, sopstveni, iskljuci_sebe=True)

        b_i = min(
            _prosecna_udaljenost(X, i, labele, k, iskljuci_sebe=False)
            for k in klasteri if k != sopstveni
        )

        skorovi[i] = (b_i - a_i) / max(a_i, b_i) if max(a_i, b_i) > 0 else 0.0

    return float(np.mean(skorovi))


def _prosecna_udaljenost(X, i, labele, klaster, iskljuci_sebe: bool) -> float:
    indeksi = np.where(labele == klaster)[0]
    if iskljuci_sebe:
        indeksi = indeksi[indeksi != i]
    if len(indeksi) == 0:
        return 0.0
    udaljenosti = np.sqrt(np.sum((X[indeksi] - X[i]) ** 2, axis=1))
    return float(np.mean(udaljenosti))


def interpretiraj_klaster(df_klaster, kolone: list[str]) -> str:
    """Generiše kratku tekstualnu interpretaciju klastera na osnovu proseka
    cene i tehničkih karakteristika (npr. 'jeftiniji proizvodi lošijih
    energetskih klasa')."""
    prosecna_cena = df_klaster["cena"].mean()
    delovi = [f"prosečna cena ≈ {prosecna_cena:,.0f} RSD"]

    if "energetska_klasa_num" in df_klaster.columns:
        prosecna_klasa = df_klaster["energetska_klasa_num"].mean()
        opis = "boljih" if prosecna_klasa >= 6 else "lošijih"
        delovi.append(f"{opis} energetskih klasa (prosek {prosecna_klasa:.1f}/10)")

    return ", ".join(delovi)
