"""
Izvor: market.metalac.com (statički HTML, bez anti-bot zaštite).

Listing daje 40 kartica/strani (naziv + cena + link). Specifikacije (energetska
klasa, kapacitet, zapremina...) su na stranici proizvoda, pa se ona dohvata
posebno — slično tehnomaniji, ali bez Cloudflare-a pa može više workera.

Zajednički interfejs za orchestrator: run(upsert_fn, log, stop_event).
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup
from curl_cffi import requests

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from zajednicko.util import ENERGETSKE_KLASE  # noqa: E402

BASE = "https://www.market.metalac.com"
IZVOR = "metalac.rs"
WORKERS = 10
STRANA_TIMEOUT = 180
MAX_STRANA = 100

# slug -> naziv kategorije (usklađeno sa ostalim izvorima)
KATEGORIJE = {
    "kombinovani-frizideri": "frizider",
    "frizideri-sa-jednim-vratima": "frizider",
    "side-by-side-frizideri": "frizider",
    "ugradni-frizideri": "frizider",
    "horizontalni-zamrzivaci": "zamrzivac",
    "vertikalni-zamrzivaci": "zamrzivac",
    "masine-za-ves-sa-prednjim-punjenjem": "ves_masina",
    "masine-za-ves-sa-punjenjem-odozgo": "ves_masina",
    "masine-za-pranje-i-susenje-vesa": "ves_masina",
    "masine-za-susenje-vesa": "susilica",
    "samostojece-sudomasine": "masina_za_sudove",
    "ugradne-sudomasine": "masina_za_sudove",
    "elektricni-sporeti": "sporet",
    "kombinovani-sporeti": "sporet",
    "plinski-sporeti": "sporet",
    "ugradne-rerne": "ugradna_rerna",
    "ugradne-ploce": "ugradna_ploca",
    "samostalni-aspiratori": "aspirator",
    "ugradni-aspiratori": "aspirator",
    "samostalne-mikrotalasne": "mikrotalasna",
    "ugradne-mikrotalasne": "mikrotalasna",
    "bojleri": "bojler",
    "malolitrazni-bojleri": "bojler",
    "radijatori-i-grejalice": "grejno_telo",
    "masine-za-meso": "masina_za_meso",
}

_KLASE_SET = {k.upper() for k in ENERGETSKE_KLASE}
_SESSION = requests.Session(impersonate="chrome120")


def _broj(tekst: str):
    m = re.search(r"(\d+(?:[.,]\d+)?)", tekst.replace(".", "").replace(",", "."))
    return float(m.group(1)) if m else None


def _specs(tekst: str) -> dict:
    """Izvlači tehničke atribute iz teksta stranice proizvoda (regex)."""
    out = {}
    m = re.search(r"Energetsk\w+\s+(?:klas\w+|razred)[:\s]*([A-G](?:\+{1,3})?)", tekst, re.I)
    if m and m.group(1).upper() in _KLASE_SET:
        out["energetska_klasa"] = m.group(1).upper()
    m = re.search(r"Kapacitet[^:]{0,25}[:\s]+([\d.,]+)\s*kg", tekst, re.I)
    if m:
        out["kapacitet_kg"] = _broj(m.group(1) + " kg")
    m = re.search(r"(?:Zapremina|Bruto zapremina|Neto zapremina)[^:]{0,25}[:\s]+([\d.,]+)\s*(?:l\b|lit)", tekst, re.I)
    if m:
        out["zapremina_l"] = _broj(m.group(1))
    m = re.search(r"(?:Snaga|Priključna snaga)[^:]{0,25}[:\s]+([\d.,]+)\s*W", tekst, re.I)
    if m:
        out["snaga_w"] = _broj(m.group(1))
    m = re.search(r"Dijagonala[^:]{0,25}[:\s]+([\d.,]+)", tekst, re.I)
    if m:
        out["dijagonala_inch"] = _broj(m.group(1))
    return out


def _kartice(html: str) -> list[tuple[str, str, float | None]]:
    """Vraća (url, naziv, cena) za svaku karticu na listing strani."""
    soup = BeautifulSoup(html, "lxml")
    rez = []
    for c in soup.select("div.product"):
        a = c.select_one("h3.product-name a")
        if not a or not a.get("href"):
            continue
        cena_el = c.select_one(".product-price")
        cena = _broj(cena_el.get_text(strip=True)) if cena_el else None
        rez.append((a["href"], a.get_text(strip=True), cena))
    return rez


def _proizvod(url: str, naziv: str, cena: float | None, naziv_kat: str) -> dict | None:
    try:
        r = _SESSION.get(url, timeout=25)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "lxml")
    specs = _specs(soup.get_text(" ", strip=True))
    brend = naziv.split()[0] if naziv else None
    return {
        "izvor": IZVOR,
        "izvorni_id": None,
        "url": url,
        "naziv": naziv,
        "brend": brend,
        "kategorija": naziv_kat,
        "podkategorija": None,
        "cena": cena,
        "cena_pre_akcije": None,
        "na_lageru": True,
        "energetska_klasa": specs.get("energetska_klasa"),
        "dijagonala_inch": specs.get("dijagonala_inch"),
        "kapacitet_kg": specs.get("kapacitet_kg"),
        "zapremina_l": specs.get("zapremina_l"),
        "snaga_w": specs.get("snaga_w"),
        "sve_karakteristike": specs,
    }


def discover():
    print(f"Metalac — provera {len(KATEGORIJE)} kategorija\n")
    for slug, naziv in KATEGORIJE.items():
        r = _SESSION.get(f"{BASE}/{slug}/1", timeout=20)
        n = len(_kartice(r.text)) if r.status_code == 200 else 0
        print(f"  [{'OK' if n else 'PRAZNO'}]  {naziv:<18} {n} na 1. strani  /{slug}")


def run(upsert_fn, log=print, stop_event=None) -> int:
    ukupno = 0
    for slug, naziv in KATEGORIJE.items():
        if stop_event and stop_event.is_set():
            break
        page = 1
        while page <= MAX_STRANA:
            if stop_event and stop_event.is_set():
                log("prekinuto (watchdog)")
                return ukupno
            r = _SESSION.get(f"{BASE}/{slug}/{page}", timeout=20)
            if r.status_code != 200:
                break
            kartice = _kartice(r.text)
            if not kartice:
                break
            ok = 0
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                futs = [pool.submit(_proizvod, u, n, c, naziv) for u, n, c in kartice]
                try:
                    for fut in as_completed(futs, timeout=STRANA_TIMEOUT):
                        p = fut.result()
                        if p and p["cena"]:
                            upsert_fn(p)
                            ok += 1
                            ukupno += 1
                except TimeoutError:
                    for f in futs:
                        f.cancel()
                    log(f"{naziv} str.{page}: TIMEOUT — preskačem kategoriju")
                    break
            log(f"{naziv} str.{page}: {ok}/{len(kartice)} upisano (ukupno: {ukupno})")
            page += 1
    log(f"GOTOVO — {ukupno} sa Metalca.")
    return ukupno


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--discover", action="store_true")
    g.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.discover:
        discover()
    else:
        sys.path.append(str(Path(__file__).resolve().parent))
        from db import upsert_proizvod, broj_zapisa
        run(upsert_proizvod)
        print(f"Ukupno u bazi: {broj_zapisa()}")
