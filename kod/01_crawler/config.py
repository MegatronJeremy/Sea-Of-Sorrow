"""
Konfiguracija veb indeksera za https://www.tehnomanija.rs

Sajt je rađen u Magento-u, što znači:
  - listing stranice koriste paginaciju preko ?p=N query parametra
  - kartica proizvoda na listing stranici ima klasu "product-item-info"
  - stranica proizvoda ima tabelu specifikacija
    "table.additional-attributes-wrapper" sa th.col.label / td.col.data parovima
  - cena je u <span data-price-amount="...">
  - dostupnost je u <div class="stock available|unavailable">

Pokriveno istraživanjem strukture sajta (curl + ručni pregled HTML-a),
videti komentare uz svaku kategoriju za status provere.
"""

BASE_URL = "https://www.tehnomanija.rs"

# slug (putanja iza domena) -> (naziv kategorije koji ide u bazu, podkategorija)
# Popuniti/proširiti po potrebi nakon --discover provere.
KATEGORIJE: dict[str, str] = {
    "bela-tehnika/frizideri": "frizider",
    "bela-tehnika/zamrzivaci": "zamrzivac",
    "bela-tehnika/ves-masine": "ves_masina",
    "bela-tehnika/masine-za-sudove": "masina_za_sudove",
    "bela-tehnika/sporeti": "sporet",
    "bela-tehnika/ugradne-rerne-i-ploce": "ugradna_rerna",
    "bela-tehnika/mikrotalasne": "mikrotalasna",
    "bela-tehnika/aspiratori": "aspirator",
    "bela-tehnika/bojleri": "bojler",
    "tv-foto-audio-i-video/televizori": "televizor",
}

# Najveći broj stranica po kategoriji koji se obilazi (zaštita od beskonačnog crawl-a;
# povećati za pun --run nakon što se sve provери na malom broju stranica).
MAX_STRANICA_PO_KATEGORIJI = 200

# Throttling: nasumična pauza između HTTP zahteva, u sekundama.
PAUZA_MIN_S = 1.5
PAUZA_MAX_S = 3.5

# Broj pokušaja i eksponencijalni backoff pri grešci (timeout, 429, 5xx).
MAX_POKUSAJA = 4
BACKOFF_BAZA_S = 2.0

# Rotacija User-Agent zaglavlja (smanjuje šansu za blokiranje/throttling na serveru).
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

IZVOR_NAZIV = "tehnomanija.rs"

# CSS selektori (Magento) korišćeni u parser.py — na jednom mestu, lako za izmenu
# ako Tehnomanija promeni temu/verziju Magento-a.
SELECTORS = {
    "product_card": "li.product-item, div.product-item-info",
    "product_link": "a.product-item-link",
    "pagination_next": "a.action.next",
    "title": 'span.base[data-ui-id="page-title-wrapper"]',
    "price_amount": "span[data-price-amount]",
    "stock": "div.stock",
    "specs_table": "table.additional-attributes-wrapper, table.data.table.additional-attributes",
    "specs_row": "tr",
    "specs_label": "th.col.label",
    "specs_value": "td.col.data",
    "brand": 'a[href*="/brend/"], div.product-brand, span.brand',
}
