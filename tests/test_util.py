"""
Testovi za kod/zajednicko/util.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from zajednicko.util import (
    ENERGETSKE_KLASE,
    cenovni_opseg,
    energetska_klasa_u_broj,
    normalizuj,
    standardizuj,
)


class TestEnergetskiKlasaUBroj:
    def test_poznate_klase(self):
        assert energetska_klasa_u_broj("G") == 1
        assert energetska_klasa_u_broj("A") == 7
        assert energetska_klasa_u_broj("A+") == 8
        assert energetska_klasa_u_broj("A++") == 9
        assert energetska_klasa_u_broj("A+++") == 10

    def test_case_insensitive(self):
        assert energetska_klasa_u_broj("a+++") == 10
        assert energetska_klasa_u_broj("g") == 1

    def test_none_vraca_none(self):
        assert energetska_klasa_u_broj(None) is None

    def test_prazno_vraca_none(self):
        assert energetska_klasa_u_broj("") is None

    def test_nepoznata_vraca_none(self):
        assert energetska_klasa_u_broj("Z") is None
        assert energetska_klasa_u_broj("A++++") is None

    def test_redosled_je_rastuci(self):
        vrednosti = [energetska_klasa_u_broj(k) for k in ENERGETSKE_KLASE]
        assert vrednosti == sorted(vrednosti)

    def test_whitespace_se_trimuje(self):
        assert energetska_klasa_u_broj("  A+  ") == 8


class TestCenovniOpseg:
    def test_do_30k(self):
        assert cenovni_opseg(15_000) == "≤ 30.000"
        assert cenovni_opseg(30_000) == "≤ 30.000"

    def test_srednji_opseg(self):
        assert cenovni_opseg(30_001) == "30.001–100.000"
        assert cenovni_opseg(99_999) == "30.001–100.000"

    def test_viši_opseg(self):
        assert cenovni_opseg(100_001) == "100.001–300.000"
        assert cenovni_opseg(299_999) == "100.001–300.000"

    def test_skupi(self):
        assert cenovni_opseg(300_001) == "≥ 300.000"
        assert cenovni_opseg(1_000_000) == "≥ 300.000"


class TestNormalizuj:
    def test_raspon_0_do_1(self):
        s = pd.Series([0.0, 5.0, 10.0])
        n = normalizuj(s)
        assert n.min() == pytest.approx(0.0)
        assert n.max() == pytest.approx(1.0)

    def test_konstanta_vraca_nule(self):
        s = pd.Series([5.0, 5.0, 5.0])
        n = normalizuj(s)
        assert (n == 0.0).all()

    def test_duzina_sacuvana(self):
        s = pd.Series(range(20))
        assert len(normalizuj(s)) == 20


class TestStandardizuj:
    def test_sredina_oko_nule(self):
        rng = np.random.default_rng(0)
        s = pd.Series(rng.normal(100, 15, 1000))
        z = standardizuj(s)
        assert z.mean() == pytest.approx(0.0, abs=0.01)

    def test_std_oko_jedan(self):
        rng = np.random.default_rng(0)
        s = pd.Series(rng.normal(50, 10, 1000))
        z = standardizuj(s)
        assert z.std() == pytest.approx(1.0, abs=0.02)

    def test_nulta_std_vraca_nule(self):
        s = pd.Series([3.14, 3.14, 3.14])
        z = standardizuj(s)
        assert (z == 0.0).all()
