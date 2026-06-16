"""
Upis prikupljenih proizvoda u primarnu bazu (tabela proizvodi_primarna).
Koristi UPSERT (ON CONFLICT po url koloni) da ponovno pokretanje crawler-a
ne pravi duplikate, već ažurira cenu/dostupnost postojećih zapisa.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # da nađe zajednicko/
from zajednicko.db import cursor  # noqa: E402

_UPSERT_SQL = """
INSERT INTO proizvodi_primarna (
    izvor, izvorni_id, url, naziv, brend, kategorija, podkategorija,
    cena, cena_pre_akcije, na_lageru, energetska_klasa,
    dijagonala_inch, kapacitet_kg, zapremina_l, snaga_w, sve_karakteristike
) VALUES (
    %(izvor)s, %(izvorni_id)s, %(url)s, %(naziv)s, %(brend)s, %(kategorija)s, %(podkategorija)s,
    %(cena)s, %(cena_pre_akcije)s, %(na_lageru)s, %(energetska_klasa)s,
    %(dijagonala_inch)s, %(kapacitet_kg)s, %(zapremina_l)s, %(snaga_w)s, %(sve_karakteristike)s
)
ON CONFLICT (url) DO UPDATE SET
    cena             = EXCLUDED.cena,
    cena_pre_akcije  = EXCLUDED.cena_pre_akcije,
    na_lageru        = EXCLUDED.na_lageru,
    sve_karakteristike = EXCLUDED.sve_karakteristike,
    datum_preuzimanja  = now();
"""


def upsert_proizvod(proizvod: dict) -> None:
    proizvod = dict(proizvod)  # ne mutiraj originalni rečnik
    proizvod["sve_karakteristike"] = json.dumps(
        proizvod.get("sve_karakteristike") or {}, ensure_ascii=False
    )
    with cursor() as cur:
        cur.execute(_UPSERT_SQL, proizvod)


def broj_zapisa() -> int:
    with cursor() as cur:
        cur.execute("SELECT count(*) FROM proizvodi_primarna;")
        return cur.fetchone()[0]
