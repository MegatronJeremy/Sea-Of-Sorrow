"""
Orchestrator veb indeksera. Tri režima rada:

    python crawler.py --discover
        Proverava koje kategorije iz config.KATEGORIJE postoje na sajtu
        (HTTP 200) i koliko stranica/proizvoda ima svaka — bez upisa u bazu.

    python crawler.py --test --kat frizider
        Preuzima samo PRVU stranicu jedne kategorije i ispisuje parsirane
        podatke za nekoliko proizvoda (bez upisa u bazu) — za proveru selektora.

    python crawler.py --run [--kat frizider] [--max-stranica 50]
        Pun crawl (sve ili izabrana kategorija) sa upisom u bazu.
        Pošten prema serveru: throttling + rotacija UA, videti config.py.

Pre punog --run obavezno odraditi --discover i --test, i po potrebi
podesiti CSS selektore u config.SELECTORS.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from config import BASE_URL, KATEGORIJE, MAX_STRANICA_PO_KATEGORIJI  # noqa: E402
from fetcher import Fetcher  # noqa: E402
from parser import apsolutni_url, parsiraj_listing, parsiraj_proizvod  # noqa: E402


def discover():
    fetcher = Fetcher()
    print(f"Provera {len(KATEGORIJE)} kategorija na {BASE_URL} ...\n")
    for slug, naziv in KATEGORIJE.items():
        url = f"{BASE_URL}/{slug}"
        resp = fetcher.get(url)
        if resp is None:
            print(f"  [NE RADI]  {naziv:<22} {url}")
            continue
        linkovi, sledeca = parsiraj_listing(resp.text)
        status = "OK" if linkovi else "OK (0 proizvoda — provери selektore)"
        print(f"  [{status}]  {naziv:<22} {url}  -> {len(linkovi)} proizvoda na 1. strani"
              f"{', ima sledeću stranicu' if sledeca else ''}")


def test(kategorija_naziv: str, broj_primera: int = 5):
    slug = _slug_za_naziv(kategorija_naziv)
    fetcher = Fetcher()
    url = f"{BASE_URL}/{slug}"
    print(f"Test kategorije '{kategorija_naziv}': {url}\n")

    resp = fetcher.get(url)
    if resp is None:
        print("Nije uspelo preuzimanje listing stranice.")
        return

    linkovi, _ = parsiraj_listing(resp.text)
    print(f"Pronađeno {len(linkovi)} proizvoda na prvoj strani. Parsiram prvih {broj_primera}:\n")

    for href in linkovi[:broj_primera]:
        url_proizvoda = apsolutni_url(href)
        resp_p = fetcher.get(url_proizvoda)
        if resp_p is None:
            print(f"  [GREŠKA] {url_proizvoda}")
            continue
        podaci = parsiraj_proizvod(resp_p.text, url_proizvoda, kategorija_naziv)
        if podaci is None:
            print(f"  [NIJE PREPOZNATO] {url_proizvoda}")
            continue
        print(f"  • {podaci['naziv']}")
        print(f"      brend={podaci['brend']!r}  cena={podaci['cena']}  "
              f"energ.klasa={podaci['energetska_klasa']!r}  na_lageru={podaci['na_lageru']}")
        print(f"      ({len(podaci['sve_karakteristike'])} tehničkih karakteristika pronađeno)\n")


def _auto_workers() -> int:
    """Broj workera: 16 (I/O-bound task — ako sajt blokira sa 403, smanji --workers)."""
    return 16


def run(kategorija_naziv: str | None, max_stranica: int, workers: int = 0):
    # uvoz db.py odmah pre upisa, kako --discover/--test ne bi zahtevali konekciju na bazu
    from db import broj_zapisa, upsert_proizvod

    if workers <= 0:
        workers = _auto_workers()

    _counter_lock = threading.Lock()
    _zavrseno = 0

    def _preuzmi_i_parsiraj(href: str, naziv: str, ukupno: int) -> tuple[int, dict | None]:
        nonlocal _zavrseno
        fetcher_local = Fetcher()
        url_proizvoda = apsolutni_url(href)
        resp_p = fetcher_local.get(url_proizvoda)
        with _counter_lock:
            _zavrseno += 1
            br = _zavrseno
            print(f"  [{br:>2}/{ukupno}] preuzeto...", end="\r", flush=True)
        if resp_p is None:
            return br, None
        podaci = parsiraj_proizvod(resp_p.text, url_proizvoda, naziv)
        return br, podaci

    fetcher = Fetcher()
    stavke = list(KATEGORIJE.items())
    if kategorija_naziv:
        stavke = [(s, n) for s, n in KATEGORIJE.items() if n == kategorija_naziv]
        if not stavke:
            print(f"Nepoznata kategorija: {kategorija_naziv}")
            return

    print(f"Paralelni crawl — {workers} workera (auto: {os.cpu_count()} CPU jezgara).\n")
    ukupno_upisano = 0

    for slug, naziv in stavke:
        print(f"\n=== Kategorija: {naziv} ({slug}) ===")
        url = f"{BASE_URL}/{slug}"
        stranica = 1

        while url and stranica <= max_stranica:
            resp = fetcher.get(url)
            if resp is None:
                break

            linkovi, sledeca = parsiraj_listing(resp.text)
            n = len(linkovi)
            print(f"  Strana {stranica}: {n} proizvoda", flush=True)

            # reset brojaca za ovu stranicu
            with _counter_lock:
                _zavrseno = 0

            rezultati: dict[int, dict | None] = {}
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {
                    pool.submit(_preuzmi_i_parsiraj, href, naziv, n): i
                    for i, href in enumerate(linkovi, 1)
                }
                for future in as_completed(futures):
                    redni, podaci = future.result()
                    rezultati[redni] = podaci

            # ispis u redu i upis u bazu
            print(" " * 40, end="\r")  # obrisi progress liniju
            ok = greska = 0
            for _, podaci in sorted(rezultati.items()):
                if podaci:
                    naziv_kratko = podaci["naziv"][:55]
                    print(f"    OK  {naziv_kratko}")
                    upsert_proizvod(podaci)
                    ukupno_upisano += 1
                    ok += 1
                else:
                    greska += 1
            print(f"  => {ok} upisano, {greska} greška  (ukupno u sesiji: {ukupno_upisano})")

            url = apsolutni_url(sledeca) if sledeca else None
            stranica += 1

    print(f"\nGotovo. Upisano/ažurirano {ukupno_upisano} proizvoda u ovoj sesiji.")
    print(f"Ukupan broj zapisa u primarnoj bazi: {broj_zapisa()}")


def _slug_za_naziv(naziv: str) -> str:
    for slug, n in KATEGORIJE.items():
        if n == naziv:
            return slug
    raise SystemExit(
        f"Nepoznata kategorija '{naziv}'. Dostupne: {', '.join(KATEGORIJE.values())}"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupa = ap.add_mutually_exclusive_group(required=True)
    grupa.add_argument("--discover", action="store_true", help="provери koje kategorije postoje")
    grupa.add_argument("--test", action="store_true", help="testiraj parsiranje jedne kategorije")
    grupa.add_argument("--run", action="store_true", help="pun crawl sa upisom u bazu")
    ap.add_argument("--kat", help="naziv kategorije iz config.KATEGORIJE (vrednosti rečnika)")
    ap.add_argument("--max-stranica", type=int, default=MAX_STRANICA_PO_KATEGORIJI)
    ap.add_argument("--workers", type=int, default=4,
                    help="broj paralelnih workera za preuzimanje proizvoda (default: 4)")
    args = ap.parse_args()

    if args.discover:
        discover()
    elif args.test:
        if not args.kat:
            raise SystemExit("--test zahteva --kat <naziv_kategorije>")
        test(args.kat)
    elif args.run:
        run(args.kat, args.max_stranica, args.workers)
