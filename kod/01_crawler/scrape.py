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
import metalac  # noqa: E402
from db import broj_zapisa, upsert_proizvod  # noqa: E402

# naziv -> run funkcija (run(upsert_fn, log, stop_event) -> int)
IZVORI = {
    "gigatron": gigatron.run,
    "tehnomanija": tehnomanija.run,
    "metalac": metalac.run,
}
DEFAULT = ["gigatron", "tehnomanija", "metalac"]

# Ako izvor ne zabeleži napredak (ne pozove log) duže od ovoga — watchdog ga prekida.
STALL_TIMEOUT = 240   # sekundi bez napretka = zaglavljen
WATCHDOG_TICK = 20    # koliko često watchdog proverava

_lock = threading.Lock()
_poslednji: dict[str, float] = {}   # naziv -> vreme poslednjeg napretka
_stop: dict[str, threading.Event] = {}


def _log_za(tag: str):
    def log(poruka: str):
        _poslednji[tag] = time.time()   # svaki log = dokaz napretka
        with _lock:
            print(f"[{tag:<11}] {poruka}", flush=True)
    return log


_zavrseni: set[str] = set()   # izvori koji su uredno završili (watchdog ih ignoriše)


def _watchdog(izabrani: list[str], kraj: threading.Event):
    """Prekida izvor koji nema napretka duže od STALL_TIMEOUT (osim ako je već završio)."""
    while not kraj.wait(WATCHDOG_TICK):
        sada = time.time()
        for n in izabrani:
            if n in _zavrseni or _stop[n].is_set():
                continue
            zastoj = sada - _poslednji.get(n, sada)
            if zastoj > STALL_TIMEOUT:
                with _lock:
                    print(f"[watchdog   ] '{n}' bez napretka {zastoj:.0f}s — PREKID", flush=True)
                _stop[n].set()


def pokreni(izabrani: list[str]) -> None:
    print(f"Paralelni scrape: {', '.join(izabrani)}  (watchdog: prekid posle {STALL_TIMEOUT}s zastoja)\n")
    t0 = time.time()
    rezultati: dict[str, object] = {}
    for n in izabrani:
        _poslednji[n] = time.time()
        _stop[n] = threading.Event()

    kraj = threading.Event()
    wd = threading.Thread(target=_watchdog, args=(izabrani, kraj), daemon=True)
    wd.start()

    with ThreadPoolExecutor(max_workers=len(izabrani)) as pool:
        futs = {pool.submit(IZVORI[n], upsert_proizvod, _log_za(n), stop_event=_stop[n]): n
                for n in izabrani}
        for fut in as_completed(futs):
            n = futs[fut]
            _zavrseni.add(n)   # uredno završio — watchdog ga više ne dira
            try:
                rezultati[n] = fut.result()
            except Exception as e:
                rezultati[n] = f"GRESKA: {e}"
    kraj.set()

    print("\n=== Rezime ===")
    for n, r in rezultati.items():
        oznaka = "  (prekinut watchdog-om)" if (_stop[n].is_set() and n not in _zavrseni) else ""
        print(f"  {n:<12} {r}{oznaka}")
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
