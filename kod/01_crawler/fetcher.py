"""
HTTP sloj veb indeksera: preuzimanje stranica sa throttling-om, rotacijom
User-Agent zaglavlja i eksponencijalnim backoff-om pri grešci.

Cilj: ne opteretiti server izvornog sajta (poštovanje uslova korišćenja,
izbegavanje DoS efekta) — videti config.PAUZA_MIN_S / PAUZA_MAX_S.
"""
from __future__ import annotations

import random
import time

import requests

from config import BACKOFF_BAZA_S, MAX_POKUSAJA, PAUZA_MAX_S, PAUZA_MIN_S, USER_AGENTS


class Fetcher:
    def __init__(self):
        self.session = requests.Session()

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "sr-RS,sr;q=0.9,en;q=0.8",
        }

    def get(self, url: str, **kwargs) -> requests.Response | None:
        """GET zahtev sa retry/backoff logikom. Vraća None ako svi pokušaji propadnu."""
        for pokusaj in range(1, MAX_POKUSAJA + 1):
            try:
                resp = self.session.get(
                    url, headers=self._headers(), timeout=20, **kwargs
                )
                if resp.status_code == 200:
                    self._throttle()
                    return resp
                if resp.status_code == 429 or resp.status_code >= 500:
                    self._backoff(pokusaj)
                    continue
                # 404 i slične greške nema smisla ponavljati
                print(f"  [fetcher] HTTP {resp.status_code} za {url}")
                return None
            except requests.RequestException as e:
                print(f"  [fetcher] greška ({pokusaj}/{MAX_POKUSAJA}) za {url}: {e}")
                self._backoff(pokusaj)
        return None

    @staticmethod
    def _throttle():
        time.sleep(random.uniform(PAUZA_MIN_S, PAUZA_MAX_S))

    @staticmethod
    def _backoff(pokusaj: int):
        time.sleep(BACKOFF_BAZA_S ** pokusaj + random.uniform(0, 1))
