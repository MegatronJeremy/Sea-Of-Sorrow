"""
Veb parser: izdvaja podatke iz HTML stranica kategorija i pojedinačnih
proizvoda sa tehnomanija.rs (Magento platforma).

Tehnika: HTML/DOM parsiranje pomoću BeautifulSoup, uz regularne izraze
za izdvajanje numeričkih vrednosti (inch, kg, litar, W) iz tehničkih
karakteristika koje su date kao slobodan tekst.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from config import BASE_URL, SELECTORS

# Regex obrasci za izdvajanje numeričkih vrednosti iz teksta specifikacija,
# npr. "55 inča" -> 55.0, "8 kg" -> 8.0, "350 l" -> 350.0
_RE_BROJ = re.compile(r"(\d+(?:[.,]\d+)?)")


def _broj_iz_teksta(tekst: str | None) -> float | None:
    if not tekst:
        return None
    m = _RE_BROJ.search(tekst.replace(".", "").replace(",", "."))
    return float(m.group(1)) if m else None


def parsiraj_listing(html: str) -> tuple[list[str], str | None]:
    """Iz HTML-a stranice kategorije izdvaja:
    - listu URL-ova proizvoda na toj stranici
    - URL sledeće stranice (paginacija), ili None ako je poslednja
    """
    soup = BeautifulSoup(html, "html.parser")

    linkovi = []
    for a in soup.select(SELECTORS["product_link"]):
        href = a.get("href")
        if href:
            linkovi.append(href)
    # ukloni duplikate, zadrži redosled
    linkovi = list(dict.fromkeys(linkovi))

    sledeca = soup.select_one(SELECTORS["pagination_next"])
    sledeca_url = sledeca.get("href") if sledeca else None

    return linkovi, sledeca_url


def parsiraj_proizvod(html: str, url: str, kategorija: str) -> dict | None:
    """Iz HTML-a stranice proizvoda izdvaja sve relevantne atribute.

    Vraća rečnik spreman za upis u tabelu `proizvodi_primarna`
    (vidi baza/01_schema_primarna.sql), ili None ako stranica ne sadrži
    prepoznatljiv proizvod (npr. promenjen template, stranica skinuta sa sajta).
    """
    soup = BeautifulSoup(html, "html.parser")

    naziv_el = soup.select_one(SELECTORS["title"])
    if not naziv_el:
        return None
    naziv = naziv_el.get_text(strip=True)

    cena_el = soup.select_one(SELECTORS["price_amount"])
    cena = None
    if cena_el and cena_el.get("data-price-amount"):
        try:
            cena = float(cena_el["data-price-amount"])
        except ValueError:
            cena = None

    stock_el = soup.select_one(SELECTORS["stock"])
    na_lageru = None
    if stock_el:
        klase = stock_el.get("class", [])
        na_lageru = "available" in klase

    brend = _izdvoj_brend(soup, naziv)

    karakteristike = _izdvoj_specifikacije(soup)

    return {
        "izvor": "tehnomanija.rs",
        "izvorni_id": _izdvoj_id_iz_url(url),
        "url": url,
        "naziv": naziv,
        "brend": brend,
        "kategorija": kategorija,
        "podkategorija": None,
        "cena": cena,
        "cena_pre_akcije": None,
        "na_lageru": na_lageru,
        "energetska_klasa": _nadji_karakteristiku(
            karakteristike, ["energetska klasa", "energetska klasa (eu 2021)"]
        ),
        "dijagonala_inch": _broj_iz_teksta(
            _nadji_karakteristiku(karakteristike, ["dijagonala ekrana", "dijagonala"])
        ),
        "kapacitet_kg": _broj_iz_teksta(
            _nadji_karakteristiku(karakteristike, ["kapacitet pranja", "kapacitet"])
        ),
        "zapremina_l": _broj_iz_teksta(
            _nadji_karakteristiku(
                karakteristike, ["zapremina", "zapremina frižidera", "ukupna zapremina"]
            )
        ),
        "snaga_w": _broj_iz_teksta(
            _nadji_karakteristiku(karakteristike, ["snaga", "rashladna snaga"])
        ),
        "sve_karakteristike": karakteristike,
    }


def _izdvoj_id_iz_url(url: str) -> str | None:
    # tehnomanija URL-ovi se često završavaju na "-<broj>" (sku/id proizvoda)
    m = re.search(r"-(\d+)/?$", url)
    return m.group(1) if m else None


def _izdvoj_brend(soup: BeautifulSoup, naziv: str) -> str | None:
    el = soup.select_one(SELECTORS["brand"])
    if el:
        tekst = el.get_text(strip=True)
        if tekst:
            return tekst
    # fallback: brend je obično prva reč u nazivu proizvoda (konvencija Magento prodavnica)
    if naziv:
        return naziv.split()[0]
    return None


def _izdvoj_specifikacije(soup: BeautifulSoup) -> dict:
    """Parsira tabelu sa tehničkim karakteristikama u rečnik {naziv: vrednost}."""
    tabela = soup.select_one(SELECTORS["specs_table"])
    rezultat: dict[str, str] = {}
    if not tabela:
        return rezultat

    for red in tabela.select(SELECTORS["specs_row"]):
        label_el = red.select_one(SELECTORS["specs_label"])
        value_el = red.select_one(SELECTORS["specs_value"])
        if label_el and value_el:
            kljuc = label_el.get_text(strip=True).lower()
            if kljuc in SPECS_REDOVI_ZA_IGNORISANJE:
                # "Import Specifikacija" i slični redovi sadrže ugnježdenu
                # tabelu proizvođača spojenu u jedan blob teksta (više
                # ključeva nalepljenih jedan na drugi) — nepouzdano za
                # strukturirano parsiranje, preskačemo ih.
                continue
            vrednost = value_el.get_text(strip=True)
            if kljuc and vrednost:
                rezultat[kljuc] = vrednost
    return rezultat


# Redovi u tabeli specifikacija koji sadrže "blob" tekst umesto čistog
# key-value para (videti komentar iznad) i koje treba ignorisati.
SPECS_REDOVI_ZA_IGNORISANJE = {"import specifikacija"}


def _nadji_karakteristiku(karakteristike: dict, moguci_kljucevi: list[str]) -> str | None:
    for kljuc in moguci_kljucevi:
        if kljuc in karakteristike:
            return karakteristike[kljuc]
    return None


def apsolutni_url(href: str) -> str:
    if href.startswith("http"):
        return href
    return BASE_URL.rstrip("/") + "/" + href.lstrip("/")
