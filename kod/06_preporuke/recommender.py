"""
Zadatak 6: Content-based recommender system — ručna implementacija
(TF-IDF, kosinusna sličnost i sortiranje su samostalno kodirani;
scikit-learn se NE koristi za cosine_similarity, kao što zahteva postavka).

Profil proizvoda (feature vector) kombinuje:
  - numeričke atribute (cena, dijagonala/kapacitet/zapremina/snaga, energ. klasa) — standardizovani
  - brend — One-Hot Encoding
  - naziv proizvoda — ručni TF-IDF (term frequency-inverse document frequency)

Sličnost: kosinusna sličnost između feature vektora (ručna implementacija
skalarnog proizvoda i intenziteta vektora, bez sklearn-a).
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np
import pandas as pd


# --- Ručni TF-IDF nad nazivima proizvoda ---

def _tokenizuj(tekst: str) -> list[str]:
    return [t.lower() for t in tekst.replace("-", " ").split() if len(t) > 1]


def izgradi_tfidf_matricu(nazivi: pd.Series) -> np.ndarray:
    """Ručna TF-IDF implementacija.

    TF(term, dok)   = broj_pojavljivanja(term, dok) / broj_termina(dok)
    IDF(term)       = log(N / broj_dokumenata_koji_sadrze_term)
    TF-IDF(term, d) = TF(term, d) * IDF(term)
    """
    dokumenti = [_tokenizuj(n) for n in nazivi]
    N = len(dokumenti)

    # rečnik svih termina
    svi_termini = sorted(set(t for doc in dokumenti for t in doc))
    indeks_termina = {t: i for i, t in enumerate(svi_termini)}

    # IDF po terminu
    broj_dokumenata_sa_termom = Counter()
    for doc in dokumenti:
        for t in set(doc):
            broj_dokumenata_sa_termom[t] += 1
    idf = {
        t: math.log(N / broj_dokumenata_sa_termom[t]) if broj_dokumenata_sa_termom[t] else 0.0
        for t in svi_termini
    }

    matrica = np.zeros((N, len(svi_termini)))
    for i, doc in enumerate(dokumenti):
        if not doc:
            continue
        brojac = Counter(doc)
        for term, broj in brojac.items():
            tf = broj / len(doc)
            matrica[i, indeks_termina[term]] = tf * idf[term]

    return matrica


# --- Ručna kosinusna sličnost ---

def kosinusna_slicnost(v1: np.ndarray, v2: np.ndarray) -> float:
    """cos(theta) = (v1 . v2) / (||v1|| * ||v2||) — ručna implementacija."""
    skalarni_proizvod = float(np.dot(v1, v2))
    intenzitet1 = math.sqrt(float(np.dot(v1, v1)))
    intenzitet2 = math.sqrt(float(np.dot(v2, v2)))
    if intenzitet1 == 0 or intenzitet2 == 0:
        return 0.0
    return skalarni_proizvod / (intenzitet1 * intenzitet2)


class ContentBasedRecommender:
    """Preporuke na osnovu sličnosti feature vektora, unutar iste kategorije."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.reset_index(drop=True)
        self.feature_matrica = self._izgradi_feature_matricu(self.df)

    def _izgradi_feature_matricu(self, df: pd.DataFrame) -> np.ndarray:
        numericke_kolone = ["cena", "energetska_klasa_num", "dijagonala_inch",
                             "kapacitet_kg", "zapremina_l", "snaga_w"]
        numericke = df[numericke_kolone].fillna(0)
        numericke = (numericke - numericke.mean()) / numericke.std().replace(0, 1)

        brend_one_hot = pd.get_dummies(df["brend"])
        tfidf_naziv = izgradi_tfidf_matricu(df["naziv"])

        return np.hstack([
            numericke.values,
            brend_one_hot.values,
            tfidf_naziv,
        ])

    def preporuci(self, proizvod_id: int, top_n: int = 5) -> pd.DataFrame:
        """Vraća top_n najsličnijih proizvoda IZ ISTE KATEGORIJE kao izabrani."""
        idx = self.df.index[self.df["id"] == proizvod_id]
        if len(idx) == 0:
            raise ValueError(f"Proizvod sa id={proizvod_id} nije pronađen.")
        idx = idx[0]

        kategorija = self.df.loc[idx, "kategorija"]
        kandidati = self.df.index[(self.df["kategorija"] == kategorija) & (self.df.index != idx)]

        vektor_izabranog = self.feature_matrica[idx]
        slicnosti = [
            (i, kosinusna_slicnost(vektor_izabranog, self.feature_matrica[i]))
            for i in kandidati
        ]
        slicnosti.sort(key=lambda x: x[1], reverse=True)
        top_indeksi = [i for i, _ in slicnosti[:top_n]]
        top_skorovi = [s for _, s in slicnosti[:top_n]]

        rezultat = self.df.loc[top_indeksi, ["id", "naziv", "brend", "cena"]].copy()
        rezultat["slicnost"] = top_skorovi
        return rezultat.reset_index(drop=True)
