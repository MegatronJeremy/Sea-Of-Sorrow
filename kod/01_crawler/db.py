"""
Upis prikupljenih proizvoda u primarnu bazu (tabela proizvodi_primarna).
Koristi UPSERT (ON CONFLICT po url koloni) da ponovno pokretanje crawler-a
ne pravi duplikate, već ažurira cenu/dostupnost postojećih zapisa.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.db import cursor  # noqa: E402

# SQLite koristi :ime za named parametre (umesto %(ime)s)
_UPSERT_SQL = """
INSERT INTO proizvodi_primarna (
    izvor, izvorni_id, url, naziv, brend, kategorija, podkategorija,
    cena, cena_pre_akcije, na_lageru, energetska_klasa,
    dijagonala_inch, kapacitet_kg, zapremina_l, snaga_w, sve_karakteristike
) VALUES (
    :izvor, :izvorni_id, :url, :naziv, :brend, :kategorija, :podkategorija,
    :cena, :cena_pre_akcije, :na_lageru, :energetska_klasa,
    :dijagonala_inch, :kapacitet_kg, :zapremina_l, :snaga_w, :sve_karakteristike
)
ON CONFLICT(url) DO UPDATE SET
    cena               = excluded.cena,
    cena_pre_akcije    = excluded.cena_pre_akcije,
    na_lageru          = excluded.na_lageru,
    sve_karakteristike = excluded.sve_karakteristike,
    datum_preuzimanja  = datetime('now');
"""


def upsert_proizvod(proizvod: dict) -> None:
    proizvod = dict(proizvod)
    proizvod["sve_karakteristike"] = json.dumps(
        proizvod.get("sve_karakteristike") or {}, ensure_ascii=False
    )
    if isinstance(proizvod.get("na_lageru"), bool):
        proizvod["na_lageru"] = int(proizvod["na_lageru"])
    with cursor() as cur:
        cur.execute(_UPSERT_SQL, proizvod)


def broj_zapisa() -> int:
    with cursor() as cur:
        cur.execute("SELECT count(*) FROM proizvodi_primarna;")
        return cur.fetchone()[0]
