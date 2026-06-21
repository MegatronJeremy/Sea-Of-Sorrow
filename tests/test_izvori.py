"""
Testovi za nove izvore (gigatron, metalac) — čiste funkcije za mapiranje i
ekstrakciju, bez mrežnih zahteva. conftest.py dodaje kod/01_crawler na sys.path.
"""
from __future__ import annotations

import json

import gigatron
import metalac


# ── gigatron ──────────────────────────────────────────────────────────────────

class TestGigatronBroj:
    def test_broj_sa_jedinicom(self):
        assert gigatron._broj("86 W") == 86.0

    def test_broj_decimala_zarez(self):
        assert gigatron._broj("8,5 kg") == 8.5

    def test_broj_hiljade_tacka(self):
        assert gigatron._broj("12.000") == 12000.0

    def test_broj_bez_broja(self):
        assert gigatron._broj("nema") is None


class TestGigatronMapiraj:
    def _raw(self):
        return {
            "productName": "GORENJE RF414EPS4 Kombinovani frižider",
            "productReference": "3838782525551",
            "brand": "Gorenje",
            "link": "/gorenje-rf414eps4-frizider/p",
            "categories": ["/Bela tehnika/Frižideri/"],
            "priceRange": {
                "sellingPrice": {"highPrice": 23999, "lowPrice": 23999},
                "listPrice": {"highPrice": 25999, "lowPrice": 25999},
            },
            "specificationGroups": [{
                "specifications": [
                    {"name": "Energetska klasa", "values": ["E - Novo"]},
                    {"name": "Zapremina frižidera", "values": ["165 l"]},
                    {"name": "Priključna snaga", "values": ["86 W"]},
                ]
            }],
        }

    def test_osnovna_polja(self):
        p = gigatron.mapiraj(self._raw(), "frizider")
        assert p["naziv"].startswith("GORENJE")
        assert p["brend"] == "Gorenje"
        assert p["kategorija"] == "frizider"
        assert p["izvor"] == "gigatron.rs"
        assert p["url"].startswith("https://gigatron.rs/")

    def test_cena_i_akcija(self):
        p = gigatron.mapiraj(self._raw(), "frizider")
        assert p["cena"] == 23999.0
        assert p["cena_pre_akcije"] == 25999.0  # listPrice > sellingPrice

    def test_specifikacije_izvucene(self):
        p = gigatron.mapiraj(self._raw(), "frizider")
        assert p["energetska_klasa"] == "E"       # "E - Novo" -> "E"
        assert p["zapremina_l"] == 165.0
        assert p["snaga_w"] == 86.0

    def test_bez_naziva_vraca_none(self):
        assert gigatron.mapiraj({"productName": ""}, "frizider") is None


class TestGigatronIzvuciProizvode:
    def test_izvlaci_iz_rsc_payload(self):
        proizvod = {"productName": "Test frižider", "productReference": "111",
                    "brand": "Test", "priceRange": {"sellingPrice": {"lowPrice": 100}}}
        unutra = json.dumps(proizvod)                 # sadržaj RSC chunk-a
        captured = json.dumps(unutra)                 # JSON-string-enkodiran
        html = f"self.__next_f.push([1,{captured}])"
        rez = gigatron.izvuci_proizvode(html)
        assert len(rez) == 1
        assert rez[0]["productName"] == "Test frižider"

    def test_dedup_po_referenci(self):
        p = {"productName": "X", "productReference": "999"}
        unutra = json.dumps(p) + json.dumps(p)  # isti proizvod dvaput
        captured = json.dumps(unutra)
        html = f"self.__next_f.push([1,{captured}])"
        assert len(gigatron.izvuci_proizvode(html)) == 1


# ── metalac ───────────────────────────────────────────────────────────────────

class TestMetalacSpecs:
    def test_energetski_razred(self):
        assert metalac._specs("Energetski razred: E")["energetska_klasa"] == "E"

    def test_energetska_klasa_sa_plus(self):
        assert metalac._specs("Energetska klasa A++")["energetska_klasa"] == "A++"

    def test_kapacitet_kg(self):
        assert metalac._specs("Kapacitet punjenja: 8 kg")["kapacitet_kg"] == 8.0

    def test_zapremina_l(self):
        assert metalac._specs("Zapremina: 242 l")["zapremina_l"] == 242.0

    def test_snaga_w(self):
        assert metalac._specs("Snaga: 2000 W")["snaga_w"] == 2000.0

    def test_prazno_kad_nema(self):
        assert metalac._specs("Boja: bela") == {}


class TestMetalacKartice:
    def test_parsira_karticu(self):
        html = """
        <div class="product">
          <h3 class="product-name"><a href="https://x.rs/frizider-1.html">Vox frižider KG2730E</a></h3>
          <span class="product-price">19.990RSD</span>
        </div>
        <div class="product">
          <h3 class="product-name"><a href="https://x.rs/frizider-2.html">Beko frižider RDSO</a></h3>
          <span class="product-price">22.499RSD</span>
        </div>
        """
        kartice = metalac._kartice(html)
        assert len(kartice) == 2
        url, naziv, cena = kartice[0]
        assert url == "https://x.rs/frizider-1.html"
        assert naziv == "Vox frižider KG2730E"
        assert cena == 19990.0

    def test_prazan_html(self):
        assert metalac._kartice("<div>nema proizvoda</div>") == []
