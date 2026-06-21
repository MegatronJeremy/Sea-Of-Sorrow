"""
Izvor: tehnomanija.rs (statički Magento HTML).

Zajednički interfejs za orchestrator: run(upsert_fn, log).
Listing daje samo linkove → svaka stranica proizvoda se dohvata posebno
(zato je sporiji od gigatrona). Paralelizuje preuzimanje proizvoda po strani.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import BASE_URL, KATEGORIJE, MAX_STRANICA_PO_KATEGORIJI
from fetcher import Fetcher
from parser import apsolutni_url, parsiraj_listing, parsiraj_proizvod

WORKERS = 6  # max koji tehnomanija tolerise bez 403


def run(upsert_fn, log=print, workers: int = WORKERS) -> int:
    fetcher = Fetcher()
    ukupno = 0

    def _preuzmi(href: str, naziv: str):
        f = Fetcher()
        url = apsolutni_url(href)
        resp = f.get(url)
        if resp is None:
            return None
        return parsiraj_proizvod(resp.text, url, naziv)

    for slug, naziv in KATEGORIJE.items():
        url = f"{BASE_URL}/{slug}"
        stranica = 1
        while url and stranica <= MAX_STRANICA_PO_KATEGORIJI:
            resp = fetcher.get(url)
            if resp is None:
                break
            linkovi, sledeca = parsiraj_listing(resp.text)
            if not linkovi:
                break
            ok = 0
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futs = [pool.submit(_preuzmi, h, naziv) for h in linkovi]
                for fut in as_completed(futs):
                    p = fut.result()
                    if p:
                        upsert_fn(p)
                        ok += 1
                        ukupno += 1
            log(f"{naziv} str.{stranica}: {ok}/{len(linkovi)} upisano (ukupno: {ukupno})")
            url = apsolutni_url(sledeca) if sledeca else None
            stranica += 1

    log(f"GOTOVO — {ukupno} sa Tehnomanije.")
    return ukupno
