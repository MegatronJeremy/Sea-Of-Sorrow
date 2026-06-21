"""
Orchestrator za prikupljanje sa više izvora — PARALELNO (jedan thread po sajtu).

Pošto su izvori različiti serveri, paralelno pokretanje ne povećava opterećenje
ni jednom sajtu (nema dodatnog rizika od bana), a ukupno vreme ≈ najsporiji sajt.
Svaki izvor je modul sa zajedničkim interfejsom:  run(upsert_fn, log) -> int

Dodavanje novog sajta = novi modul + jedan red u IZVORI.

Pokretanje:
    python scrape.py                          # svi default izvori
    python scrape.py --izvori gigatron        # samo izabrani
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))           # config/fetcher/parser/db
sys.path.append(str(Path(__file__).resolve().parents[1]))        # zajednicko

import gigatron  # noqa: E402
import tehnomanija  # noqa: E402
from db import broj_zapisa, upsert_proizvod  # noqa: E402

# naziv -> run funkcija (run(upsert_fn, log) -> int)
IZVORI = {
    "gigatron": gigatron.run,
    "tehnomanija": tehnomanija.run,
}
DEFAULT = ["gigatron", "tehnomanija"]

_lock = threading.Lock()


def _log_za(tag: str):
    def log(poruka: str):
        with _lock:
            print(f"[{tag:<11}] {poruka}", flush=True)
    return log


def pokreni(izabrani: list[str]) -> None:
    print(f"Paralelni scrape: {', '.join(izabrani)}\n")
    t0 = time.time()
    rezultati: dict[str, object] = {}

    with ThreadPoolExecutor(max_workers=len(izabrani)) as pool:
        futs = {pool.submit(IZVORI[n], upsert_proizvod, _log_za(n)): n for n in izabrani}
        for fut in as_completed(futs):
            n = futs[fut]
            try:
                rezultati[n] = fut.result()
            except Exception as e:
                rezultati[n] = f"GRESKA: {e}"

    print("\n=== Rezime ===")
    for n, r in rezultati.items():
        print(f"  {n:<12} {r}")
    print(f"\nUkupno u primarnoj bazi: {broj_zapisa()}")
    print(f"Vreme: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--izvori", default=",".join(DEFAULT),
                    help=f"zarezom razdvojeni izvori. dostupni: {', '.join(IZVORI)}")
    args = ap.parse_args()
    izabrani = [s.strip() for s in args.izvori.split(",") if s.strip() in IZVORI]
    if not izabrani:
        raise SystemExit(f"Nepoznati izvori. Dostupni: {', '.join(IZVORI)}")
    pokreni(izabrani)
