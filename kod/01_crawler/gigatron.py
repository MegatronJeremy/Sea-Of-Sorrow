"""
Drugi izvor podataka: gigatron.rs (Next.js SPA).

Za razliku od tehnomanije (statički HTML, zahtev po proizvodu), Gigatron ugrađuje
SVE proizvode jedne listing-strane zajedno sa specifikacijama u Next.js RSC payload
(self.__next_f.push(...)). Zato jedan HTTP zahtev daje ~24 proizvoda sa punim
specifikacijama — mnogo efikasnije i bez potrebe za headless browserom.

Pokretanje:
    python gigatron.py --discover     # broj proizvoda po kategoriji
    python gigatron.py --run          # pun scrape + upis u bazu
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

from curl_cffi import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.util import ENERGETSKE_KLASE  # noqa: E402

try:
    from db import broj_zapisa, upsert_proizvod
except ImportError:
    upsert_proizvod = broj_zapisa = None  # za --discover bez baze

BASE = "https://gigatron.rs"
IZVOR = "gigatron.rs"
MAX_STRANA = 200

# slug -> naziv kategorije (usklađeno sa tehnomanijom gde ima smisla)
KATEGORIJE = {
    "bela-tehnika/ves-masine": "ves_masina",
    "bela-tehnika/frizideri": "frizider",
    "bela-tehnika/zamrzivaci": "zamrzivac",
    "bela-tehnika/sporeti": "sporet",
    "bela-tehnika/masine-za-pranje-sudova": "masina_za_sudove",
    "bela-tehnika/mikrotalasne-rerne": "mikrotalasna",
    "bela-tehnika/aspiratori": "aspirator",
    "bela-tehnika/bojleri": "bojler",
    "bela-tehnika/ugradna-tehnika": "ugradna_rerna",
    "bela-tehnika/grejna-tela": "grejno_telo",
    "mali-kucni-aparati/usisivaci": "usisivac",
    "mali-kucni-aparati/pegle": "pegla",
    "mali-kucni-aparati/ventilatori": "ventilator",
    "mali-kucni-aparati/parocistaci": "parocistac",
    "mali-kucni-aparati/masine-za-sivenje": "masina_za_sivenje",
    "mali-kucni-aparati/kucni-aparati": "kucni_aparat",
    "mali-kucni-aparati/aparati-za-tretiranje-vazduha": "precistac_vazduha",
}

_KLASE_SET = {k.upper() for k in ENERGETSKE_KLASE}
_SESSION = requests.Session(impersonate="chrome120")


def _broj(tekst: str):
    """Izvlači prvi decimalni broj iz teksta npr. '86 W' -> 86.0, '8,5 kg' -> 8.5."""
    m = re.search(r"(\d+(?:[.,]\d+)?)", tekst.replace(".", "").replace(",", "."))
    return float(m.group(1)) if m else None


def izvuci_proizvode(html: str) -> list[dict]:
    """Parsira sve product objekte iz Next.js RSC payload-a stranice."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', html, flags=re.S)
    spojeno = "".join(json.loads(c) for c in chunks if c)
    dec = json.JSONDecoder()
    proizvodi, vidjeni, i = [], set(), 0
    while True:
        i = spojeno.find("{", i)
        if i < 0:
            break
        try:
            obj, kraj = dec.raw_decode(spojeno, i)
            if isinstance(obj, dict) and "productName" in obj:
                ref = obj.get("productReference")
                if ref not in vidjeni:
                    vidjeni.add(ref)
                    proizvodi.append(obj)
                i = kraj
                continue
        except Exception:
            pass
        i += 1
    return proizvodi


def mapiraj(raw: dict, naziv_kat: str) -> dict | None:
    """Mapira sirov Gigatron product objekat u šemu naše baze."""
    naziv = raw.get("productName")
    if not naziv:
        return None
    cene = raw.get("priceRange", {})
    cena = cene.get("sellingPrice", {}).get("lowPrice")
    lista = cene.get("listPrice", {}).get("highPrice")
    cena_pre = lista if (lista and cena and lista > cena) else None

    # specifikacije -> rečnik {naziv: prva vrednost}
    specs: dict[str, str] = {}
    for grupa in raw.get("specificationGroups", []):
        for s in grupa.get("specifications", []):
            vals = s.get("values") or []
            if vals:
                specs[s.get("name", "")] = str(vals[0])

    energetska = None
    dijagonala = kapacitet = zapremina = snaga = None
    for ime, vred in specs.items():
        iml = ime.lower()
        if energetska is None and "energetska klasa" in iml:
            kand = vred.strip().split()[0].upper()  # 'E - Novo' -> 'E'
            if kand in _KLASE_SET:
                energetska = kand
        elif snaga is None and "snaga" in iml:
            snaga = _broj(vred)
        elif zapremina is None and "zapremina" in iml:
            zapremina = _broj(vred)
        elif kapacitet is None and "kapacitet" in iml and "kg" in vred.lower():
            kapacitet = _broj(vred)
        elif dijagonala is None and "dijagonal" in iml:
            dijagonala = _broj(vred)

    link = raw.get("link", "")
    return {
        "izvor": IZVOR,
        "izvorni_id": str(raw.get("productReference") or ""),
        "url": BASE + link if link.startswith("/") else link,
        "naziv": naziv.strip(),
        "brend": raw.get("brand"),
        "kategorija": naziv_kat,
        "podkategorija": (raw.get("categories") or [None])[0],
        "cena": float(cena) if cena else None,
        "cena_pre_akcije": float(cena_pre) if cena_pre else None,
        "na_lageru": specs.get("Online kupovina", "Yes").lower() in ("yes", "da", "true"),
        "energetska_klasa": energetska,
        "dijagonala_inch": dijagonala,
        "kapacitet_kg": kapacitet,
        "zapremina_l": zapremina,
        "snaga_w": snaga,
        "sve_karakteristike": specs,
    }


PAUZA = (0.3, 0.8)  # throttling između zahteva (poštovanje servera, izbegavanje DoS-a)


def _strana(slug: str, page: int) -> list[dict]:
    time.sleep(random.uniform(*PAUZA))
    url = f"{BASE}/{slug}?page={page}"
    r = _SESSION.get(url, timeout=25)
    if r.status_code != 200:
        return []
    return izvuci_proizvode(r.text)


def discover():
    print(f"Gigatron — provera {len(KATEGORIJE)} kategorija\n")
    for slug, naziv in KATEGORIJE.items():
        prod = _strana(slug, 1)
        print(f"  [{'OK' if prod else 'PRAZNO'}]  {naziv:<20} {len(prod)} na 1. strani  /{slug}")


def run(upsert_fn=None, log=print, stop_event=None) -> int:
    """Scrape svih kategorija + upis. Zajednički interfejs za orchestrator:
    upsert_fn(proizvod), log(poruka), stop_event (watchdog prekid). Vraća broj upisanih."""
    if upsert_fn is None:
        upsert_fn = upsert_proizvod
    ukupno = 0
    for slug, naziv in KATEGORIJE.items():
        if stop_event and stop_event.is_set():
            break
        page = 1
        while page <= MAX_STRANA:
            if stop_event and stop_event.is_set():
                log("prekinuto (watchdog)")
                return ukupno
            proizvodi = _strana(slug, page)
            if not proizvodi:
                break
            ok = 0
            for raw in proizvodi:
                p = mapiraj(raw, naziv)
                if p and p["cena"]:
                    upsert_fn(p)
                    ok += 1
                    ukupno += 1
            log(f"{naziv} str.{page}: {ok}/{len(proizvodi)} upisano (ukupno: {ukupno})")
            page += 1
    log(f"GOTOVO — {ukupno} sa Gigatrona.")
    return ukupno


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--discover", action="store_true")
    g.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.discover:
        discover()
    else:
        run()
        if broj_zapisa:
            print(f"Ukupan broj zapisa u primarnoj bazi: {broj_zapisa()}")
