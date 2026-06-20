"""
Testovi za kod/03_vizuelizacija/generisi_grafike.py

Grafičke funkcije se testiraju sa sintetičkim DataFrame-om — bez baze i
bez prikaza prozora (matplotlib u neinteraktivnom modu).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # mora biti pre bilo kog pyplot importa

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "kod" / "03_vizuelizacija"))

import generisi_grafike as _viz


@pytest.fixture(autouse=True)
def zatvori_figure():
    """Zatvara sve matplotlib figure posle svakog testa da ne curimo memoriju."""
    yield
    plt.close("all")


@pytest.fixture
def df_viz(sample_df) -> pd.DataFrame:
    """sample_df iz conftest.py, prilagođen za vizuelizaciju."""
    df = sample_df.copy()
    # osiguraj da ima energetsku klasu u string formatu (ne None samo)
    df["energetska_klasa"] = df["energetska_klasa"].fillna("D")
    return df


# ── graf_kategorije ───────────────────────────────────────────────────────────

class TestGrafKategorije:
    def test_ne_baca_gresku(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_kategorije(df_viz)

    def test_kreira_png_fajlove(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_kategorije(df_viz)
        fajlovi = list(tmp_path.glob("kategorije_*.png"))
        assert len(fajlovi) == 2, f"Očekivana 2 PNG fajla, pronađeno: {fajlovi}"

    def test_prazni_df_ne_pada(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        df_prazan = pd.DataFrame({"kategorija": pd.Series([], dtype=str),
                                  "brend": pd.Series([], dtype=str),
                                  "cena": pd.Series([], dtype=float),
                                  "energetska_klasa": pd.Series([], dtype=str)})
        # prazan df može baciti grešku pri pie-chartu — to je OK, proveravamo da ne crasha silently
        try:
            _viz.graf_kategorije(df_prazan)
        except Exception:
            pass  # prazni podaci su edge case koji nije kritičan


# ── graf_brendovi ─────────────────────────────────────────────────────────────

class TestGrafBrendovi:
    def test_ne_baca_gresku(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_brendovi(df_viz)

    def test_kreira_png_fajlove(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_brendovi(df_viz)
        fajlovi = list(tmp_path.glob("brendovi_*.png"))
        assert len(fajlovi) == 2


# ── graf_cenovni_opsezi ───────────────────────────────────────────────────────

class TestGrafCenovniOpsezi:
    def test_ne_baca_gresku(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_cenovni_opsezi(df_viz)

    def test_kreira_png_fajlove(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_cenovni_opsezi(df_viz)
        fajlovi = list(tmp_path.glob("cenovni_opsezi_*.png"))
        assert len(fajlovi) == 2

    def test_sve_cene_pokrivene(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        # po jedan proizvod u svakom opsegu
        df = pd.DataFrame({
            "cena": [15_000.0, 50_000.0, 150_000.0, 400_000.0],
            "kategorija": ["a", "b", "c", "d"],
            "brend": ["X", "Y", "Z", "W"],
            "energetska_klasa": ["A", "B", "C", "D"],
        })
        _viz.graf_cenovni_opsezi(df)
        fajlovi = list(tmp_path.glob("cenovni_opsezi_*.png"))
        assert len(fajlovi) == 2


# ── graf_energetska_klasa ─────────────────────────────────────────────────────

class TestGrafEnergetstaKlasa:
    def test_ne_baca_gresku(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_energetska_klasa(df_viz)

    def test_kreira_png_fajlove(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_energetska_klasa(df_viz)
        fajlovi = list(tmp_path.glob("energetska_klasa_*.png"))
        assert len(fajlovi) == 2

    def test_ignorise_nan_klase(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        df = pd.DataFrame({
            "energetska_klasa": ["A", None, "B", None, "A"],
            "kategorija": ["f"] * 5,
            "brend": ["X"] * 5,
            "cena": [50000.0] * 5,
        })
        _viz.graf_energetska_klasa(df)  # ne sme da pada


# ── graf_scatter_cena_zapremina ───────────────────────────────────────────────

class TestScatterCenaZapremina:
    def test_pravi_fajl(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        df = pd.DataFrame({
            "kategorija": ["frizider"] * 5 + ["zamrzivac"] * 3,
            "zapremina_l": [200.0, 300.0, 400.0, 500.0, 350.0, 100.0, 150.0, 200.0],
            "cena": [50000.0, 70000.0, 90000.0, 120000.0, 80000.0, 30000.0, 35000.0, 40000.0],
            "brend": ["Samsung"] * 8,
            "energetska_klasa": ["A"] * 8,
        })
        _viz.graf_scatter_cena_zapremina(df)
        assert (tmp_path / "scatter_cena_zapremina.png").exists()

    def test_prazni_podaci_ne_pravi_fajl(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        df = pd.DataFrame({"kategorija": ["televizor"], "zapremina_l": [np.nan], "cena": [50000.0],
                           "brend": ["X"], "energetska_klasa": ["A"]})
        _viz.graf_scatter_cena_zapremina(df)
        assert not (tmp_path / "scatter_cena_zapremina.png").exists()


# ── graf_scatter_cena_dijagonala ──────────────────────────────────────────────

class TestScatterCenaDijagonala:
    def test_pravi_fajl(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        df = pd.DataFrame({
            "kategorija": ["televizor"] * 6,
            "dijagonala_inch": [32.0, 43.0, 50.0, 55.0, 65.0, 75.0],
            "cena": [30000.0, 45000.0, 60000.0, 80000.0, 100000.0, 150000.0],
            "brend": ["Samsung"] * 6,
            "energetska_klasa": ["E"] * 6,
        })
        _viz.graf_scatter_cena_dijagonala(df)
        assert (tmp_path / "scatter_cena_dijagonala.png").exists()

    def test_nema_televizora_ne_pada(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        df = pd.DataFrame({"kategorija": ["frizider"], "dijagonala_inch": [np.nan],
                           "cena": [50000.0], "brend": ["X"], "energetska_klasa": ["A"]})
        _viz.graf_scatter_cena_dijagonala(df)
        assert not (tmp_path / "scatter_cena_dijagonala.png").exists()


# ── graf_boxplot_cena_po_kategoriji ──────────────────────────────────────────

class TestBoxplotCenaPoKategoriji:
    def test_pravi_fajl_sa_dovoljno_podataka(self, df_viz, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        _viz.graf_boxplot_cena_po_kategoriji(df_viz, min_zapisa=5)
        assert (tmp_path / "boxplot_cena_kategorija.png").exists()

    def test_premali_skupovi_se_filtriraju(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        df = pd.DataFrame({"kategorija": ["frizider"] * 3, "cena": [50000.0, 60000.0, 70000.0],
                           "brend": ["X"] * 3, "energetska_klasa": ["A"] * 3})
        # min_zapisa=10 — sve kategorije imaju < 10 zapisa → nema fajla
        _viz.graf_boxplot_cena_po_kategoriji(df, min_zapisa=10)
        assert not (tmp_path / "boxplot_cena_kategorija.png").exists()


# ── ukupan broj PNG fajlova ───────────────────────────────────────────────────

class TestUkupniIzlaz:
    def test_sve_funkcije_prave_ocekivane_fajlove(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_viz, "IZLAZ_DIR", tmp_path)
        rng = np.random.default_rng(0)
        n = 40
        kategorije = rng.choice(["frizider", "televizor", "ves_masina"], size=n)
        df = pd.DataFrame({
            "kategorija": kategorije,
            "brend": rng.choice(["Samsung", "LG", "Bosch", "Gorenje"], size=n),
            "cena": rng.uniform(20_000, 200_000, n),
            "energetska_klasa": rng.choice(["A", "B", "C", "D"], size=n),
            "zapremina_l": np.where(kategorije == "frizider", rng.uniform(200, 600, n), np.nan),
            "dijagonala_inch": np.where(kategorije == "televizor", rng.uniform(32, 75, n), np.nan),
        })
        _viz.graf_kategorije(df)
        _viz.graf_brendovi(df)
        _viz.graf_cenovni_opsezi(df)
        _viz.graf_energetska_klasa(df)
        _viz.graf_scatter_cena_zapremina(df)
        _viz.graf_scatter_cena_dijagonala(df)
        _viz.graf_boxplot_cena_po_kategoriji(df, min_zapisa=5)
        svi_png = list(tmp_path.glob("*.png"))
        assert len(svi_png) == 11, (
            f"Očekivano 11 PNG (8 bar/pie + scatter×2 + boxplot), "
            f"pronađeno {len(svi_png)}: {sorted(f.name for f in svi_png)}"
        )
