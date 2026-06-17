"""
Zajednički fixtures za sve testove.
Svi testovi rade BEZ konekcije na bazu — koriste sintetičke podatke.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ── sys.path setup ───────────────────────────────────────────────────────────
# Direktorijumi sa modulima koji počinju cifrom ne mogu biti Python paketi,
# pa ih ručno dodajemo na sys.path ovde (jednom, za sve testove).
_KOD = Path(__file__).parent.parent / "kod"
for _subdir in ("", "01_crawler", "04_regresija", "05_klasterovanje", "06_preporuke"):
    _p = str(_KOD / _subdir) if _subdir else str(_KOD)
    if _p not in sys.path:
        sys.path.insert(0, _p)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ── HTML fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def listing_html() -> str:
    return (FIXTURES_DIR / "listing.html").read_text(encoding="utf-8")


@pytest.fixture
def proizvod_html() -> str:
    return (FIXTURES_DIR / "proizvod.html").read_text(encoding="utf-8")


@pytest.fixture
def proizvod_nedostupan_html() -> str:
    return (FIXTURES_DIR / "proizvod_nedostupan.html").read_text(encoding="utf-8")


@pytest.fixture
def prazan_html() -> str:
    return "<html><body><p>Stranica ne postoji.</p></body></html>"


# ── DataFrame fixtures (simuluju sadržaj revidirane baze) ─────────────────

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Minimalni DataFrame koji liči na proizvodi_revidirana (30 redova, 3 kategorije)."""
    rng = np.random.default_rng(42)
    n = 30
    kategorije = rng.choice(["frizider", "televizor", "ves_masina"], size=n)
    brendovi = rng.choice(["Samsung", "LG", "Bosch", "Philips", "Gorenje"], size=n)
    energ_klase_num = np.where(
        rng.random(n) > 0.2,
        rng.integers(3, 8, size=n),
        np.nan,
    )
    return pd.DataFrame({
        "id": np.arange(1, n + 1),
        "naziv": [f"{b} {k} Model-{i}" for i, (b, k) in enumerate(zip(brendovi, kategorije))],
        "brend": brendovi,
        "kategorija": kategorije,
        "cena": rng.uniform(20_000, 200_000, size=n).round(2),
        "na_lageru": rng.choice([True, False], size=n),
        "energetska_klasa": rng.choice(["A", "B", "C", "D", "E", None], size=n),
        "energetska_klasa_num": pd.array(energ_klase_num, dtype="Float64"),
        "dijagonala_inch": pd.array(
            np.where(kategorije == "televizor", rng.uniform(32, 75, n).round(1), np.nan),
            dtype="Float64",
        ),
        "kapacitet_kg": pd.array(
            np.where(kategorije == "ves_masina", rng.uniform(5, 12, n).round(1), np.nan),
            dtype="Float64",
        ),
        "zapremina_l": pd.array(
            np.where(kategorije == "frizider", rng.uniform(100, 700, n).round(1), np.nan),
            dtype="Float64",
        ),
        "snaga_w": pd.array(
            rng.choice([500.0, 1000.0, 1500.0, np.nan], size=n),
            dtype="Float64",
        ),
        "datum_preuzimanja": pd.Timestamp("2025-01-15"),
    })
