"""
HTTP sloj veb indeksera: preuzimanje stranica sa throttling-om, rotacijom
User-Agent zaglavlja i eksponencijalnim backoff-om pri gresci.

Koristi curl_cffi (Chrome TLS fingerprint) ako je dostupna, inace requests.
curl_cffi je potrebna kada sajt koristi Cloudflare Bot Management (HTTP 403).

Cilj: ne opteretiti server izvornog sajta (postovanje uslova koriscenja,
izbegavanje DoS efekta) - videti config.PAUZA_MIN_S / PAUZA_MAX_S.
"""
from __future__ import annotations

import random
import time

from config import BACKOFF_BAZA_S, MAX_POKUSAJA, PAUZA_MAX_S, PAUZA_MIN_S, USER_AGENTS

try:
    from curl_cffi import requests as curl_requests
    _CURL_DOSTUPAN = True
except ImportError:
    import requests as _requests
    _CURL_DOSTUPAN = False


class Fetcher:
    def __init__(self):
        if _CURL_DOSTUPAN:
            self.session = curl_requests.Session(impersonate="chrome120")
        else:
            import requests
            self.session = requests.Session()

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "sr-RS,sr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def get(self, url: str, **kwargs) -> object | None:
        """GET zahtev sa retry/backoff logikom. Vraca None ako svi pokusaji propadnu."""
        for pokusaj in range(1, MAX_POKUSAJA + 1):
            try:
                if _CURL_DOSTUPAN:
                    resp = self.session.get(url, timeout=20, **kwargs)
                else:
                    resp = self.session.get(url, headers=self._headers(), timeout=20, **kwargs)
                if resp.status_code == 200:
                    self._throttle()
                    return resp
                if resp.status_code in (403, 429) or resp.status_code >= 500:
                    self._backoff(pokusaj)
                    continue
                print(f"  [fetcher] HTTP {resp.status_code} za {url}")
                return None
            except Exception as e:
                print(f"  [fetcher] greska ({pokusaj}/{MAX_POKUSAJA}) za {url}: {e}")
                self._backoff(pokusaj)
        return None

    @staticmethod
    def _throttle():
        time.sleep(random.uniform(PAUZA_MIN_S, PAUZA_MAX_S))

    @staticmethod
    def _backoff(pokusaj: int):
        time.sleep(BACKOFF_BAZA_S ** pokusaj + random.uniform(0, 1))
