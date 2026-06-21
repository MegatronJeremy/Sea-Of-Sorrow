"""
Behavioralni testovi — proveravaju NAMERU (da izlaz odgovara ulazu), ne samo da
kod ne puca. Ovde žive greške tipa „funkcija ignoriše argument" koje ne ruše
ništa i daju uverljiv ali pogrešan izlaz (npr. interpretacija klastera koja je
uvek pominjala energetsku klasu bez obzira na izbor promenljivih).

Pravilo: za svaku kontrolu/argument — promeni ulaz, proveri da se izlaz promeni
na očekivani način.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from kmeans import interpretiraj_klaster
from recommender import ContentBasedRecommender
from regresija import LinearnaRegresijaGD, podeli_train_test, pripremi_podatke


@pytest.fixture
def df():
    rng = np.random.default_rng(3)
    n = 120
    kat = rng.choice(["frizider", "televizor", "ves_masina"], n)
    return pd.DataFrame({
        "id": np.arange(1, n + 1),
        "naziv": [f"Brend{i} Model {k}" for i, k in enumerate(kat)],
        "brend": rng.choice(["SAMSUNG", "LG", "BOSCH"], n),
        "kategorija": kat,
        "cena": rng.uniform(20000, 90000, n).round(0),
        "energetska_klasa_num": rng.choice([3.0, 5.0, 7.0], n),
        "dijagonala_inch": np.where(kat == "televizor", rng.uniform(32, 65, n).round(0), np.nan),
        "kapacitet_kg": np.where(kat == "ves_masina", rng.uniform(5, 12, n).round(1), np.nan),
        "zapremina_l": np.where(kat == "frizider", rng.uniform(150, 400, n).round(0), np.nan),
        "snaga_w": rng.uniform(500, 2500, n).round(0),
    })


# ── Interpretacija klastera mora da prati IZABRANE promenljive ─────────────────

class TestKlasterInterpretacijaNamera:
    """Regresioni testovi za bug: interpretacija je ignorisala `kolone`."""

    def test_cena_zapremina_pominje_zapreminu_ne_energetsku(self, df):
        g = df.dropna(subset=["zapremina_l"])
        opis = interpretiraj_klaster(g, ["cena", "zapremina_l"]).lower()
        assert "zapremin" in opis
        assert "energ" not in opis          # NIJE izabrana → ne sme da se pojavi

    def test_cena_snaga_pominje_snagu(self, df):
        opis = interpretiraj_klaster(df, ["cena", "snaga_w"]).lower()
        assert "snag" in opis
        assert "energ" not in opis

    def test_cena_energetska_pominje_energetsku(self, df):
        opis = interpretiraj_klaster(df, ["cena", "energetska_klasa_num"]).lower()
        assert "energ" in opis
        assert "zapremin" not in opis

    def test_cena_uvek_prisutna(self, df):
        # cena je glavni pokazatelj — uvek u opisu ako postoji
        assert "cena" in interpretiraj_klaster(df, ["snaga_w"]).lower()

    def test_razlicit_izbor_razlicit_opis(self, df):
        a = interpretiraj_klaster(df, ["cena", "snaga_w"])
        b = interpretiraj_klaster(df, ["cena", "energetska_klasa_num"])
        assert a != b                        # različite promenljive → različit tekst


# ── Recommender: izlaz mora da zavisi od upita ────────────────────────────────

class TestRecommenderNamera:
    def test_razlicit_proizvod_razlicite_preporuke(self, df):
        rec = ContentBasedRecommender(df)
        id_a = int(df[df.kategorija == "frizider"].iloc[0].id)
        id_b = int(df[df.kategorija == "televizor"].iloc[0].id)
        pa = set(rec.preporuci(id_a, 5).id)
        pb = set(rec.preporuci(id_b, 5).id)
        assert pa != pb

    def test_preporuke_iz_iste_kategorije(self, df):
        rec = ContentBasedRecommender(df)
        pid = int(df[df.kategorija == "frizider"].iloc[0].id)
        rez = rec.preporuci(pid, 5)
        kategorije = df[df.id.isin(rez.id)].kategorija.unique().tolist()
        assert kategorije == ["frizider"]

    def test_slicnost_opadajuca(self, df):
        rec = ContentBasedRecommender(df)
        pid = int(df.iloc[0].id)
        sl = rec.preporuci(pid, 5).slicnost.tolist()
        assert sl == sorted(sl, reverse=True)


# ── Regresija: promena ulaza mora da promeni predikciju ───────────────────────

class TestRegresijaNamera:
    def test_razlicit_ulaz_razlicita_predikcija(self, df):
        X, y, kolone = pripremi_podatke(df)
        Xtr, Xte, ytr, yte = podeli_train_test(X, y)
        model = LinearnaRegresijaGD(0.05, 300).fit(Xtr, ytr)
        # dve različite tačke iz test skupa daju različitu predikciju
        p = model.predict(Xte[:5])
        assert len(set(np.round(p, 2))) > 1

    def test_sve_izabrane_kolone_u_feature_matrici(self, df):
        # pripremi_podatke mora da koristi sve numeričke + one-hot kategorije/brendove
        _, _, kolone = pripremi_podatke(df)
        assert "energetska_klasa_num" in kolone
        assert any(k.startswith("kategorija_") for k in kolone)
        assert any(k.startswith("brend_") for k in kolone)
